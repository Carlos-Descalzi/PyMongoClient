import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import GObject
import pymongo
import runpy
import tempfile
import threading
from utils import JsonUtil

class DataDumper:
	
	def start(self):			pass
	def dump(self, document):	pass
	def finish(self):			pass
	
class ResultSet(GObject.GObject):
	__gsignals__ = {
		'ready' : (GObject.SIGNAL_RUN_FIRST,None, ())
	}
	def __init__(self, data, collection, last_op):
		GObject.GObject.__init__(self)
		self.data = data
		self.page = 0
		self.pages = 0
		self.collection = collection
		self.last_op = last_op
		self._ready = False
		
	def has_first(self):
		return self.page > 0
		
	def has_next(self):
		return self.page < self.pages-1
		
	def has_prev(self):
		return self.page > 0
		
	def has_last(self):
		return self.page < self.pages -1
		
	def next_page(self):
		if self.page < self.pages-1:
			self.page+=1
			self._update_page_data()
		
	def first_page(self):
		self.page = 0
		self._update_page_data()
		
	def last_page(self):
		self.page = self.pages -1
		self._update_page_data()
	
	def prev_page(self):
		if self.page > 0:
			self.page -=1
			self._update_page_data()

	def _update_page_data(self):
		self._ready = False
		def _do_run():
			self._do_update_page_data()
			self._ready = True
			self.emit('ready')
		
		self.thread = threading.Thread(target=_do_run)
		self.thread.start()

	def _do_update_page_data(self):
		raise Exception('Unimplemented')

	def create_export_job(self, dumper):
		return ResultSetExporter(self, dumper)

	def generator(self):
		pass

	def is_ready(self):
		return self._ready

class CursorResultSet(ResultSet):
	def __init__(self, data, last_op):
		ResultSet.__init__(self,data,data.collection.name,last_op)
		self.data = data
		self.totalsize = data.count()
		self.page = 0
		self.pages = self.totalsize / 20
		if self.totalsize % 20 > 0: self.pages+=1
		self.pagedata = []
		self._update_page_data()
		
	def __len__(self):
		return self.totalsize
		
	def _do_update_page_data(self):
		self.data.rewind()
		self.pagedata = list(self.data[self.page*20:(self.page+1)*20])

	def generator(self):
		self.data.rewind()
		for i in range(self.totalsize):
			doc = self.data[i]
			yield doc

class ListResultSet(ResultSet):
	def __init__(self, data, collection, last_op):
		ResultSet.__init__(self,data,collection, last_op)
		self.data = data
		self.page = 0
		self.pages = len(data) / 20
		if len(data) % 20 > 0: self.pages+=1
		self.pagedata = []
		self._update_page_data()
		
	def __len__(self):
		return len(self.data)
		
	def _do_update_page_data(self):
		self.pagedata = self.data[self.page*20:(self.page+1)*20]

	def generator(self):
		for doc in self.data:
			yield doc

class ResultSetExporter(GObject.GObject):
	__gsignals__ = {
		'started' 	: (GObject.SIGNAL_RUN_FIRST,None, ()),
		'progress'	: (GObject.SIGNAL_RUN_FIRST,None, (int,int)),
		'finished' 	: (GObject.SIGNAL_RUN_FIRST,None, ())
	}
	def __init__(self, resultset, dumper):
		GObject.GObject.__init__(self)
		self._resultset = resultset
		self._dumper = dumper
		self._thread = None
		
	def start(self):
		self._thread = threading.Thread(target=self.run)
		self._thread.start()
		
	def run(self):
		self._dumper.start()
		self.emit('started')
		
		n = 0
		total = len(self._resultset)
		
		for document in self._resultset.generator():
			self._dumper.dump(document)
			self.emit('progress',n,total)
			n+=1

		self._dumper.finish()
		self.emit('finished')
