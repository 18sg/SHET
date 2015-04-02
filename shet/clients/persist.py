from shet.client import ShetClient, shet_action

class Persist(ShetClient):
	
	root = "/persist/"
	
	def __init__(self):
		ShetClient.__init__(self)
		
		self.events = {}
	
	
	@shet_action("add_event")
	def _add_event(self, name):
		if name not in self.events:
			self.events[name] = self.add_event(name)
	
	
	@shet_action("remove_event")
	def _remove_event(self, name):
		self.remove_event(self.events[name])
		del self.events[name]
	
	
	@shet_action("raise_event")
	def _raise_event(self, name, *args):
		self.events[name](*args)


if __name__ == "__main__":
	Persist().run()
