from shet.client import ShetClient


class MetaShet(ShetClient):
	
	def __init__(self, server):
		ShetClient.__init__(self)
		self.server = server
		self.add_action("/meta/ls-r", self.ls_recursive)
		self.add_action("/meta/ls", self.ls)
	
	
	def ls_recursive(self, dir='/'):
		return self.server.fs.list_dir(dir)
	
	def ls(self, dir='/'):
		return self.server.fs.list_dir(dir, False)
