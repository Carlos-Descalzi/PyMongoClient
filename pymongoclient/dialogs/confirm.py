import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from ..utils import GladeObject


class ConfirmDialog(GladeObject):

    __gsignals__ = {'accept': (GObject.SIGNAL_RUN_FIRST, None, ())}

    def __init__(self):
        GladeObject.__init__(self, "pymongoclient/ui/ConfirmDialog.glade")

    def show(self, title, message):
        self.confirm_dialog.set_title(title)
        self.message.set_text(message)
        result = self.confirm_dialog.run()
        self.confirm_dialog.destroy()
        return result

    def _on_accept(self, src):
        self.confirm_dialog.emit('response', Gtk.ResponseType.OK)

    def _on_cancel(self, *args):
        self.confirm_dialog.emit('response', Gtk.ResponseType.CANCEL)
