import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk,GObject,GtkSource,Pango,GLib
from utils import GladeObject

class MessageDialog(GladeObject):
	
	def __init__(self):
		GladeObject.__init__(self, "ui/MessageDialog.glade")
		
	def show(self, title, message):
		self.message_dialog.set_title(title)
		self.message.set_text(message)
		self.message_dialog.run()
		
	def _on_accept(self,*args):
		self.message_dialog.destroy()
		
