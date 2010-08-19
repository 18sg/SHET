from shet.client import ShetClient, shet_action


class MetaShet(ShetClient):
	
	root = "/meta"
	
	def __init__(self, server):
		ShetClient.__init__(self)
		self.server = server
		self.add_action("/meta/ls-r", self.ls_recursive)
	
	
	def ls_recursive(self, dir='/'):
		return self.server.fs.list_dir(dir)
	
	@shet_action
	def ls(self, dir='/'):
		return self.server.fs.list_dir(dir, False)
