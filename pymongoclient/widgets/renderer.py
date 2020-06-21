__all__ = ["JsonFieldRenderer"]
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib


class FieldEditor(Gtk.HBox, Gtk.CellEditable):

    __gproperties__ = {
        "editing-canceled": (
            bool,
            "editing-canceled",
            "",
            False,
            GObject.ParamFlags.READWRITE,
        )
    }

    TYPES = ["Null", "Boolean", "Integer", "String"]

    def __init__(self):
        Gtk.HBox.__init__(self, False, 0)

        self.type_chooser = Gtk.ComboBoxText()

        for val_type in FieldEditor.TYPES:
            self.type_chooser.append_text(val_type)

        self.type_chooser.connect("changed", self._on_type_changed)
        self.null_editor = Gtk.Label("(null)")
        self.bool_editor = Gtk.CheckButton.new_with_label("")
        self.text_editor = Gtk.Entry()
        self.int_editor = Gtk.Entry()
        self.text_editor.connect("activate", self._on_text_editor_activate)
        self.int_editor.connect("activate", self._on_int_editor_activate)
        self.bool_editor.connect("toggled", self._on_bool_editor_toggled)

        self.editor_container = Gtk.EventBox()
        self.editor_container.set_visible_window(True)

        self.pack_start(self.editor_container, True, True, 0)
        self.pack_start(self.type_chooser, False, False, 0)
        self.show_all()

        self.value = None
        self._current_editor = None
        self._update_editor()
        self._disable_signal = False

    def _on_text_editor_activate(self, entry):
        self.value = entry.get_text()
        self.editing_done()

    def _on_int_editor_activate(self, entry):
        self.value = int(entry.get_text())
        self.editing_done()

    def _on_bool_editor_toggled(self, *args):
        self.value = self.bool_editor.get_active()
        self.editing_done()

    def _update_editor(self):
        self._disable_signal = True
        if self.value is None:
            self._set_editor(self.null_editor)
            self.type_chooser.set_active(0)
        elif isinstance(self.value, bool):
            self._set_editor(self.bool_editor)
            self.type_chooser.set_active(1)
            self.bool_editor.set_active(self.value)
        elif isinstance(self.value, int):
            self._set_editor(self.int_editor)
            self.type_chooser.set_active(2)
            self.int_editor.set_text(str(self.value))
        else:
            self._set_editor(self.text_editor)
            self.type_chooser.set_active(3)
            self.text_editor.set_text(str(self.value))
        self.show_all()
        self._disable_signal = False

    def _on_type_changed(self, *args):
        active = self.type_chooser.get_active()

        if active == 0:
            self._set_editor(self.null_editor)
            self.value = None
            self.editing_done()
        elif active == 1:
            self.bool_editor.set_active(False)
            self._set_editor(self.bool_editor)
        elif active == 2:
            self.int_editor.set_text("0")
            self._set_editor(self.int_editor)
        else:
            self.text_editor.set_text("")
            self._set_editor(self.text_editor)

    def _set_editor(self, editor):
        if self._current_editor:
            self.editor_container.remove(self._current_editor)
        self._current_editor = editor
        self.editor_container.add(editor)
        self.show_all()

    def do_get_property(self, prop):
        if prop.name == "editing-canceled":
            return False
        raise AttributeError("unknown property %s" % prop.name)

    def do_set_property(self, prop, val):
        if prop.name == "editing-canceled":
            pass
        raise AttributeError("unknown property %s" % prop.name)

    def set_value(self, value):
        self.value = value
        self._update_editor()

    def do_editing_done(self):
        self.hide()
        pass

    def do_remove_widget(self):
        pass

    def do_start_editing(self, event):
        pass


class JsonFieldRenderer(Gtk.CellRendererText):

    __gsignals__ = {
        "field-edited": (GObject.SIGNAL_RUN_FIRST, None, (object, object, object)),
    }

    def __init__(self):
        Gtk.CellRendererText.__init__(self)
        self.set_property("editable", True)
        self.editor = FieldEditor()
        self.editor.connect("editing-done", self._on_edit_done)
        self.edit_state = None

    def do_start_editing(self, event, widget, path, bg, cell, flags):

        model = widget.get_model()
        itr = model.get_iter(path)
        value = model.get_value(itr, 1)

        self.edit_state = (model, itr, value)

        if value is None or isinstance(value, (bool, int, str, float)):
            self.editor.set_value(value)
            self.editor.set_size_request(cell.width, cell.height)
            return self.editor

        return None

    def _on_edit_done(self, src, *args):
        if self.edit_state:
            model, itr, value = self.edit_state
            self.stop_editing(False)
            self.emit("field-edited", itr, value, self.editor.value)
            self.edit_state = None
