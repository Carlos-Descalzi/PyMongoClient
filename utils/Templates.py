import re
from bson.objectid import ObjectId
from constants import *

NL_IMPORT = """
import json

with open('%(filename)s','r') as f:
	for i,row in enumerate(f):
		log('Inserting doc #%%d' %% i)
		doc = json.loads(row)
		db['%(collection)s'].insert(doc)

"""

JSON_ARRAY_IMPORT = """
with open('%(filename)s','r') as f:
	docs = load(f)
	db['%(collection)s'].insert_many(docs)
"""

class Templates:
	
	@staticmethod
	def find_all(collection_name):
		return 'db%s.find({})' % Templates._python_friendly(collection_name)
		
	@staticmethod
	def indexes(collection_name):
		return 'db%s.index_information()' % Templates._python_friendly(collection_name)
		
	@staticmethod
	def _python_friendly(collection_name):
		if not re.match('^[a-zA-Z_][0-9a-zA-Z_]+$',collection_name):
			return "['%s']" % collection_name
		return '.%s' % collection_name
		
	@staticmethod
	def make_path(field_path):
		path_str = ''
		for item in field_path:
			#if isinstance(item,basestring):
			if len(path_str) > 0: path_str+='.'
			path_str+=str(item)
			#else:
			#	path_str+='[%s]' % item

		return path_str
		
	@staticmethod
	def _format_value(value):

		if isinstance(value,ObjectId):
			return "ObjectId('%s')" % str(value)
		
		return "'%s'" % value \
			if isinstance(value,basestring) and not 'ObjectId' in value \
			else str(value)
	
	@staticmethod
	def update(field_path, value):
		path_str = Templates.make_path(field_path)
		val_str = Templates._format_value(value)
		
		return "{'$set':{'%s':%s}}" % (path_str, val_str)
		
	@staticmethod
	def import_data(filename, collection, data_type, record_layout):
		if record_layout == RECORD_LAYOUT_JSON_ARRAY:
			return Templates._json_array_import(
				filename=filename, 
				collection=collection, 
				data_type=data_type)
		else:
			return Templates._nl_import(
				filename=filename, 
				collection=collection, 
				data_type=data_type)
			
	@staticmethod
	def _json_array_import(**kwargs):
		return JSON_ARRAY_IMPORT % kwargs
			
	@staticmethod
	def _nl_import(**kwargs):
		return NL_IMPORT % kwargs
