import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from ..utils import GladeObject


class AboutDialog(GladeObject):
    def __init__(self):
        GladeObject.__init__(self, 'ui/AboutDialog.glade')

    def show(self):
        self.dialog.run()

    def _on_close(self, *args):
        self.dialog.destroy()
