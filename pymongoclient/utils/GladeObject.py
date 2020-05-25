import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from .fileutil import locate_in_modules

class GladeObject(GObject.GObject):
    def __init__(self, filename):
        GObject.GObject.__init__(self)
        self._builder = Gtk.Builder()
        print(filename,locate_in_modules(filename))
        self._builder.add_from_file(locate_in_modules(filename))
        self._builder.connect_signals(self)

    def __getattr__(self, key):
        obj = self._builder.get_object(key)
        if obj: return obj

        raise AttributeError(key)
