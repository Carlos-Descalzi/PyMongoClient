import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk,GObject,GtkSource,Pango,GLib
from utils import GladeObject, JsonUtil, GtkUtil
from utils import SubprocessHandler
import tempfile

class Importer(SubprocessHandler):
	def __init__(self, 
			listener, 
			connection, 
			collection, 
			filename):
		SubprocessHandler.__init__(self, listener)
		self._connection = connection
		self._collection = collection
		self._filename = filename
		self.drop = False
		self.array = False
		self.file_type = 'json'
		self.header = False
		self.mode = 'insert'
		self.upsert_fields = []
		self.stop_on_error = False
		self.gzip = False
		
	def _build_command_lines(self):
		
		commands = []
		
		if self.gzip:
			
			tf = tempfile.NamedTemporaryFile(suffix='.gz',delete=False)
			
			commands+=[
				['cp',self._filename,tf.name],
				['gunzip',tf.name]
			]
			self._filename = tf.name.replace('.gz','')
		
		command = [
			'mongoimport',
			'--uri=%s' % self._connection.build_uri(),
			'--file=%s' % self._filename,
			'-c=%s' % self._collection
		]
		
		if self.drop:
			command+=['--drop']
		if self.array:
			command+=['--jsonArray']

		command+=['--type=%s' % self.file_type]

		command+=['--mode=%s' % self.mode]
		if self.mode == 'upsert' and self.upsert_fields:
			command+=['--upsertFields=%s' % ','.join(self._upsert_fields)]

		if self.header:
			command+=['--headerline']

		if self.stop_on_error:
			command+=['--stopOnError']
		
		commands.append(command)
		
		return commands

class ImportDialog(GladeObject):
		
	def __init__(self, connection, collection=None):
		GladeObject.__init__(self,"ui/ImportDialog.glade")
		self._connection = connection
		self._collection = collection
		self._running = False
		self.file_name.add_filter(GtkUtil.file_filter(['*.json','*.csv','*.json.gz','*.csv.gz']))
		
	def show(self):
		for c in sorted(self._connection.get_db().collection_names()):
			self.collection.append(c,c)
		
		if self._collection:
			self.collection.set_active_id(self._collection)
		
		self._update_actions()

		self.dialog.show()

	def _valid_data(self):
		return \
			self.file_name.get_filename() != '' \
			and self.collection.get_active_text() not in [None,''] 

	def _on_file_changed(self,*args):
		
		filename = self.file_name.get_filename()
		
		if filename:
			if '.csv' in filename.lower():
				self.file_type.set_current_page(1)
			else:
				self.file_type.set_current_page(0)
		
			self.gzip.set_active('.gz' in filename.lower()) 
		
		self._update_actions()
		
	def _update_actions(self,*args):
		if self._running:
			self.file_name.set_sensitive(False)
			self.collection.set_sensitive(False)
			self.file_type.set_sensitive(False)
			self.accept_btn.set_sensitive(False)
			self.cancel_btn.set_sensitive(False)
		else:
			valid = self._valid_data()
			self.coll_entry.set_sensitive(True)
			self.coll_entry.set_property('editable',True)
			self.file_type.set_sensitive(True)
			self.collection.set_hexpand(True)
			self.fields.set_sensitive(not self.headers.get_active())
			self.upsert_fields.set_sensitive(self.mode_upsert.get_active())
			self.accept_btn.set_sensitive(valid)
			self.cancel_btn.set_sensitive(True)
	
	def _on_accept(self,*args):
		self._run_import()

	def _on_cancel(self,*args):
		self.dialog.destroy()


	def _run_import(self):
		self._running = True
		
		filename = self.file_name.get_filename()
		collection = self.collection.get_active_text()

		self._importer = Importer(
			self,
			self._connection,
			collection,
			filename)
			
		if self.file_type.get_current_page() == 0:
			self._importer.file_type = 'json'
			self._importer.array = self.records_json_array.get_active()
		else:
			self._importer.file_type = 'csv'
			self._importer.header = self.headers.get_active()
			
		self._importer.drop = self.drop_collection.get_active()
		self._importer.stop_on_error = self.stop_on_error.get_active()
		self._importer.gzip = self.gzip.get_active()
		
		if self.mode_insert.get_active():
			self._importer.mode = 'insert'
		elif self.mode_upsert.get_active():
			self._importer.mode = 'upsert'
		else:
			self._importer.mode = 'merge'

		self.main_tabs.set_current_page(1)

		self._update_actions()
				
		self._importer.start()

	def write_log(self, message):
		GLib.idle_add(GtkUtil.text_view_append,self.log,message)
		
	def finish(self):
		self._running = False
		GLib.idle_add(self._update_actions)

