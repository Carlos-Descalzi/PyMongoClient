import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk,GObject,GtkSource,Pango,GLib

class GtkUtil:
	@staticmethod
	def text_buffer_append(text_buffer, text):
		it = text_buffer.get_end_iter()
		text_buffer.insert(it,text+'\n')

	@staticmethod
	def text_view_append(view, text):
		text_buffer = view.get_buffer()
		GtkUtil.text_buffer_append(text_buffer,text)
		GtkUtil._scroll_bottom(view)
		
	@staticmethod
	def _scroll_bottom(view):
		scroll = view.get_parent()
		adj = scroll.get_vadjustment()
		adj.set_value(adj.get_upper())

	@staticmethod
	def get_text(textview):
		buffer = textview.get_buffer()
		start = buffer.get_start_iter()
		end = buffer.get_end_iter()
		return buffer.get_text(start,end,False)

	@staticmethod
	def tool_button(stock_id,text,handler):
		btn = Gtk.ToolButton.new_from_stock(stock_id)
		btn.set_tooltip_text(text)
		btn.connect('clicked',handler)
		return btn
		
	@staticmethod
	def menu_item(label, handler):
		item = Gtk.MenuItem.new_with_label(label)
		item.connect('activate',handler)
		item.show()
		return item
		
	@staticmethod
	def file_filter(patterns):
		file_filter = Gtk.FileFilter()
		for pattern in patterns:
			file_filter.add_pattern(pattern)
		return file_filter
