import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from ..utils import GladeObject, gtkutil, SubprocessHandler, modelutil
from pymongoclient.messages import MESSAGES as messages
import json
from pymongoclient.connection.export.csv import CsvExporter
from pymongoclient.connection.export.json import JsonExporter


class ExportDialog(GladeObject):
    def __init__(self, connection, collection=None, resultset=None):
        GladeObject.__init__(self, "ui/ExportDialog.glade")
        self._connection = connection
        self._resultset = resultset
        self._collection = collection
        self._running = False
        self._exporter = None
        self._update_actions()
        self._extract_fields()

    def _extract_fields(self):
        renderer = Gtk.CellRendererToggle()
        renderer.set_property("activatable", True)
        renderer.connect("toggled", self._on_field_toggled)
        column = Gtk.TreeViewColumn("Select", renderer)
        column.add_attribute(renderer, "active", 0)
        column.set_max_width(50)
        column.set_resizable(False)
        self.fields.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Field", renderer)
        column.add_attribute(renderer, "text", 1)
        self.fields.append_column(column)

        model = Gtk.ListStore(bool, str)

        if self._resultset:
            data = self._resultset.resultset.pagedata
            l = len(self._resultset.resultset)
            row = data[0]

            fields = sorted(list(set([".".join(x) for x in self._do_extract_fields([], row)])))

            fields = [(True, "Select all")] + [(False, x) for x in fields]
            for field in fields:
                model.append(field)

        self.fields.set_model(model)

    def _do_extract_fields(self, prefix, obj):
        fields = []
        for key, val in list(obj.items()):
            if isinstance(val, dict):
                fields += self._do_extract_fields([key], val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        fields += self._do_extract_fields([key], item)
            else:
                fields.append(prefix + [key])
        return fields

    def show(self):
        self.dialog.show()

    def _on_accept(self, *args):
        self._run_export()

    def _on_cancel(self, *args):
        self.dialog.destroy()

    def _on_select_file(self, *args):
        dialog = Gtk.FileChooserDialog(
            messages.SAVE_FILE_DIALOG,
            self.dialog,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK,),
        )

        dialog.add_filter(gtkutil.file_filter(["*.json", "*.csv"]))

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.file_name.set_text(filename)

        dialog.destroy()

    def _update_actions(self, *args):

        has_file = self.file_name.get_text().strip() != ""

        self.file_name.set_sensitive(not self._running)

        self.accept.set_sensitive(not self._running and has_file)
        self.close.set_sensitive(not self._running)

    def _on_field_toggled(self, renderer, path):
        model = self.fields.get_model()
        itr = model.get_iter(path)
        is_first = model.iter_previous(itr) is None
        active = not renderer.get_active()
        model.set_value(itr, 0, active)

        if is_first:
            if active:
                itr = model.iter_next(itr)
                while itr:
                    model.set_value(itr, 0, False)
                    itr = model.iter_next(itr)
        else:
            first_itr = model.get_iter_first()
            model.set_value(first_itr, 0, False)

    def _get_fields(self):
        model = self.fields.get_model()
        fields = []
        all_fields = False

        for i, itr in enumerate(modelutil.iterator(model)):
            if i == 0:
                if model.get_value(itr, 0):
                    all_fields = True
            else:
                if all_fields or model.get_value(itr, 0):
                    fields.append(model.get_value(itr, 1))

        return fields

    def _run_export(self):
        self._running = True

        filename = self.file_name.get_text()
        self._exporter = self._get_exporter()
        self._exporter.export(filename)

    def _get_exporter(self, file_type):
        file_type = self.export_type_tab.get_current_page()

        if file_type == TYPE_JSON:
            exporter = JsonExporter(self._resultset.resultset)
        else:
            exporter = CsvExporter(self._resultset.resultset)

        return exporter

    def write_log(self, message):
        GLib.idle_add(gtkutil.text_view_append, self.log, message)

    def finish(self):
        self._running = False
        GLib.idle_add(self._update_actions)
