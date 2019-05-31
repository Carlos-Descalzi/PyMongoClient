from threading import Thread
from subprocess import Popen,PIPE
import select
import time
class SubprocessHandler:
	
	def __init__(self, listener):
		self._listener = listener
		self._thread = None
		self._pipe = None

	def log(self, message):
		self._listener.write_log(message)
		
	def finish(self,*args):
		self._listener.finish()
		
	def start(self):
		self._thread = Thread(target=self._run,args=(self._build_command_lines(),))
		self._thread.start()
		
	def _build_command_line(self):
		return []
		
	def _run(self, commands):
		
		for command in commands:
			self.log('Running command: %s' % ' '.join(command))
			try:
				self._pipe = Popen(command,stdout = PIPE, stderr = PIPE)

				return_codde = None

				while return_code is None:
					
					self._pipe.poll()

					return_code = self._pipe.returncode
						
					stdout, stderr = self._pipe.stdout,self._pipe.stderr
						
					ready,_,_ = select.select((stdout,stderr),(),(),.1)
					
					for fobj in ready:
						self.log(fobj.readline().strip())

					time.sleep(.1)
					
				self.log('Exited with return code %s' % return_code)
				
			except Exception as e:
				self.log('Error exporting: %s' % e.message)
			
		self.finish()
		
