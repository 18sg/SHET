from shet.client import ShetClient
from shet.sync import make_sync

from pickle import dump, load


class Bind(ShetClient):
	
	def __init__(self):
		self.root = "/bind"
		self.db = "bind.db"
		ShetClient.__init__(self)
		
		self.add_action("persistant", self.persistant_bind)
		self.add_action("once", self.once_bind)
		
		self.add_action("ls", self.ls)
		self.add_action("rm", self.rm)
		
		self.bindings = {}
		self.load_bindings()
	
	
	def store_bindings(self):
		b = [(k, w.persistant) for k,w in self.bindings.iteritems()]
		print b
		dump(b, open(self.db, "w"))
	
	
	def load_bindings(self):
		try:
			for binding, persistant in load(open(self.db, "r")):
				self.bind(binding[0], binding[1], persistant, store = False)
		except IOError:
			pass
	
	
	def persistant_bind(self, event, action):
		self.bind(event, action, True)
	
	
	def once_bind(self, event, action):
		self.bind(event, action, False)
	
	
	def bind(self, event, action, persistant, store = True):
		binding = (event, action)
		
		if binding in self.bindings:
			raise Exception("Binding already present.")
		
		def on_event(*args):
			print "evt", binding, args
			if not persistant:
				self.unwatch_event(self.bindings.pop(binding))
				self.store_bindings()
			self.act(action, *args)
		
		watcher = self.watch_event(event, on_event)
		# Inject a variable to make ls more informative. You didn't see that...
		watcher.persistant = persistant
		
		self.bindings[binding] = watcher
		if store:
			self.store_bindings()
	
	
	def ls(self):
		return [(binding, "persistant" if watcher.persistant else "once")
		        for binding, watcher in self.bindings.iteritems()]
	
	
	def rm(self, event, action):
		self.unwatch_event(self.bindings.pop((event, action)))


if __name__ == "__main__":
	Bind().run()
