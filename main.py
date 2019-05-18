import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk,GObject,GtkSource,Pango
from mongoclient import MainWindow

		
if __name__ == '__main__':
	w = MainWindow()
	w.show()
	Gtk.main()
