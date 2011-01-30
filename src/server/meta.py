from shet.client import ShetClient, shet_action


class MetaShet(ShetClient):
	
	root = "/meta"
	
	def __init__(self, server):
		ShetClient.__init__(self)
		self.server = server
		self.server.fs.on_change = self.add_event("on_tree_change")
	
	
	@shet_action("ls-r")
	def ls_recursive(self, dir='/'):
		return self.server.fs.list_dir(dir)
	
	@shet_action
	def ls(self, dir='/'):
		return self.server.fs.list_dir(dir, False)
	
	@shet_action
	def type(self, loc='/'):
		return self.server.fs.get_node(loc).type

