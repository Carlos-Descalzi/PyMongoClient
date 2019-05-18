

class DatabaseWrapper:
	
	def __init__(self, db):
		self._db = db
		self._last_ref_collection = None
		
	def __getitem__(self, key):
		self._last_ref_collection = CollectionWrapper(self._db[key])
		return self._last_ref_collection

	def __getattr__(self, key):
		self._last_ref_collection = CollectionWrapper(self._db[key])
		return self._last_ref_collection
		
	def last_ref_collection(self):
		return self._last_ref_collection
		
class MethodWrapper:
	def __init__(self, target, method):
		self._target = target
		self._method = method
		self._args = None
		self._kwargs = None
		self._result = None
		
	def __call__(self,*args,**kwargs):
		self._args = args
		self._kwargs = kwargs
		self._result = self._method(self._target,*args,**kwargs)
		return self._result
		
	def args(self):
		return self._args, self._kwargs
		
	def result(self):
		return self._result
		
class CollectionWrapper:
	def __init__(self, collection):
		self._collection = collection
		self._last_op = None
		
	def __getattr__(self, key):
		try:
			member = self._collection.__class__.__dict__[key]
			if type(member).__name__ == 'function':
				self._last_op = MethodWrapper(self._collection, member)
				return self._last_op
			return MethodWrapper(self._collection, member)
		except KeyError as e:
			return self._collection.__dict__[key]
			
	def last_op(self):
		return self._last_op
