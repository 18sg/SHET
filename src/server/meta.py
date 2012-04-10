from shet.client import ShetClient, shet_action
from functools import partial


class MetaShet(ShetClient):
	
	root = "/meta"
	
	def __init__(self, server):
		ShetClient.__init__(self)
		self.server = server
		
		# Various meta events.
		self.server.fs.on_change = self.add_event("on_tree_change")
		self.server.fs.on_raise = self.add_event("on_raise")
		self.server.fs.on_eventcreated = self.add_event("on_eventcreated")
		self.server.fs.on_eventdeleted = self.add_event("on_eventdeleted")
		self.server.fs.on_set = self.add_event("on_set")
		self.server.fs.on_get = self.add_event("on_get")
		self.server.fs.on_call = self.add_event("on_call")
		
		# Add an event that aggregates the above events.
		on_activity = self.add_event("on_activity")
		self.watch_event("on_tree_change", partial(on_activity, "tree_change"))
		self.watch_event("on_raise", partial(on_activity, "raise"))
		self.watch_event("on_eventcreated", partial(on_activity, "eventcreated"))
		self.watch_event("on_eventdeleted", partial(on_activity, "eventdeleted"))
		self.watch_event("on_set", partial(on_activity, "set"))
		self.watch_event("on_get", partial(on_activity, "get"))
		self.watch_event("on_call", partial(on_activity, "call"))
	
	
	@shet_action("ls-r")
	def ls_recursive(self, dir='/'):
		return self.server.fs.list_dir(dir)
	
	@shet_action
	def ls(self, dir='/'):
		return self.server.fs.list_dir(dir, False)
	
	@shet_action
	def type(self, loc='/'):
		return self.server.fs.get_node(loc).type
	
	@shet_action("connections/list")
	def list_connections(self):
		"""Get a dictionary mapping from connection id to a list of paths owned by
		that connection.
		"""
		return dict((conn.connection_id,
		             [node.path for node in conn.fs_nodes])
		            for conn
		            in self.server.connections)
	
	@shet_action("connections/disconnect")
	def disconnect_connection(self, connection_id):
		"""Disconnect a connection given it's id."""
		self.server.disconnect_id(connection_id)
	
	@shet_action("connections/owner")
	def find_owner(self, path):
		"""Get the id of the connection that registered the given path."""
		return self.server.fs.get_node(path).owner.connection_id
