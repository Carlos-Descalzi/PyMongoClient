import sys

version = sys.version_info.major * 10 + sys.version_info.minor
if version < 35:
	sys.stderr.write('This program only works on Python >= 3.5\n')
	sys.exit(1)

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk,GObject,GtkSource,Pango
from mongoclient import MainWindow

		
if __name__ == '__main__':
	w = MainWindow()
	w.show()
	Gtk.main()
