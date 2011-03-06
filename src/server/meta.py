from shet.client import ShetClient, shet_action
from shet.sync   import make_sync
from functools   import partial

# XXX: This should be shared with file_system.py -- not sure where to put it
def is_meta(path):
	return path.startswith("/meta/")

class MetaShet(ShetClient):
	
	root = "/meta"
	
	def __init__(self, server):
		ShetClient.__init__(self)
		self.server = server
		
		# Various meta events.
		self.server.fs.on_change       = self.add_event("on_tree_change")
		self.server.fs.on_raise        = self.add_event("on_any_raise")
		self.server.fs.on_eventcreated = self.add_event("on_any_eventcreated")
		self.server.fs.on_eventdeleted = self.add_event("on_any_eventdeleted")
		self.server.fs.on_set          = self.add_event("on_any_set")
		self.server.fs.on_get          = self.add_event("on_any_get")
		self.server.fs.on_call         = self.add_event("on_any_call")
		
		# Add an event that aggregates the above events.
		on_activity = self.add_event("on_activity")
		self.watch_event("on_tree_change",      partial(on_activity, "tree_change"))
		self.watch_event("on_any_raise",        partial(on_activity, "raise"))
		self.watch_event("on_any_eventcreated", partial(on_activity, "eventcreated"))
		self.watch_event("on_any_eventdeleted", partial(on_activity, "eventdeleted"))
		self.watch_event("on_any_set",          partial(on_activity, "set"))
		self.watch_event("on_any_get",          partial(on_activity, "get"))
		self.watch_event("on_any_call",         partial(on_activity, "call"))
		
		# Meta-Tree Management
		self.watch_event("on_tree_change", self.on_tree_change)
		self.watch_event("on_any_raise",   self.on_raise)
		self.watch_event("on_any_call",    self.on_call)
		self.watch_event("on_any_set",     self.on_set)
		self.watch_event("on_any_get",     self.on_get)
		
		# Meta tree structures which contain events etc. related to each node
		self.meta_action = {}
		self.meta_event = {}
		self.meta_property = {}
	
	
	@shet_action("ls-r")
	def ls_recursive(self, dir='/'):
		return self.server.fs.list_dir(dir)
	
	@shet_action
	def ls(self, dir='/'):
		return self.server.fs.list_dir(dir, False)
	
	@shet_action
	def type(self, loc='/'):
		return self.server.fs.get_node(loc).type
	
	@make_sync
	def on_tree_change(self, change_type, loc):
		if not is_meta(loc):
			if change_type == "add":
				type = (yield self.call("/meta/type", loc))
				if   type == "action":   self.add_meta_action(loc)
				elif type == "event":    self.add_meta_event(loc)
				elif type == "prop": self.add_meta_property(loc)
			elif change_type == "remove":
				# XXX: Checking here is a bit dodgey and highlights the need for a
				# slight refactoring
				if   loc in self.meta_action:   self.remove_meta_action(loc)
				elif loc in self.meta_event:    self.remove_meta_event(loc)
				elif loc in self.meta_property: self.remove_meta_property(loc)
		yield
	
	def add_meta_action(self, loc):
		on_call = self.add_event("on_call%s"%loc)
		self.meta_action[loc] = on_call
	
	def add_meta_event(self, loc):
		on_raise = self.add_event("on_raise%s"%loc)
		self.meta_event[loc] = on_raise
	
	def add_meta_property(self, loc):
		on_get = self.add_event("on_get%s"%loc)
		on_set = self.add_event("on_set%s"%loc)
		self.meta_property[loc] = (on_get, on_set)
	
	def remove_meta_action(self, loc):
		self.remove_event(self.meta_action[loc])
		del self.meta_action[loc]
	
	def remove_meta_event(self, loc):
		self.remove_event(self.meta_event[loc])
		del self.meta_event[loc]
	
	def remove_meta_property(self, loc):
		map(self.remove_event, self.meta_property[loc])
		del self.meta_property[loc]
	
	
	def on_raise(self, path, *args):
		self.meta_action[path](*args)
	def on_call(self, path, *args):
		self.meta_event[path](*args)
	def on_get(self, path, *args):
		self.meta_property[path][0](*args)
	def on_set(self, path, *args):
		self.meta_property[path][1](*args)
