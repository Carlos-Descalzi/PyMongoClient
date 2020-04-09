import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from ..utils import GladeObject, GtkUtil


class FieldEditorDialog(GladeObject):
    def __init__(self):
        GladeObject.__init__(self, "client/ui/FieldEditDialog.glade")

    __gsignals__ = {'accept': (GObject.SIGNAL_RUN_FIRST, None, ())}

    def show(self, field_name='', field_value='', disable_name=False):
        self.field_name.set_text(field_name)

        if disable_name:
            self.field_name.set_sensitive(False)

        if field_value is None:
            self.field_type.set_active(0)
        elif isinstance(field_value, bool):
            self.field_type.set_active(1)
            self.field_boolean_value.set_active(field_value)
        elif isinstance(field_value, int):
            self.field_type.set_active(2)
            self.field_value.get_buffer().set_text(str(field_value))
        else:
            self.field_type.set_active(3)
            self.field_value.get_buffer().set_text(str(field_value))
        self._on_field_type_change()

        self.field_type.connect('changed', self._on_field_type_change)

        self.editor_dialog.show()

    def _on_field_type_change(self, *args):
        item = self.field_type.get_active()

        if item == 0:
            self.field_value.set_sensitive(False)
            self.field_boolean_value.set_sensitive(False)
        elif item == 1:
            self.field_value.set_sensitive(False)
            self.field_boolean_value.set_sensitive(True)
        else:
            self.field_value.set_sensitive(True)
            self.field_boolean_value.set_sensitive(False)

    def get_field_name(self):
        return self.field_name.get_text()

    def get_field_value(self):
        item = self.field_type.get_active()

        if item == 0: return None
        elif item == 1: return self.field_boolean_value.get_active()
        elif item == 2: return int(self.field_value.get_buffer().get_text())
        else: return GtkUtil.get_text(self.field_value)

    def _on_accept(self, *args):
        self.emit('accept')
        self.editor_dialog.destroy()

    def _on_cancel(self, *args):
        self.editor_dialog.destroy()
