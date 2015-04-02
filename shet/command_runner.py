

class CommandNotFound(Exception):
	pass



class CommandRunnerMixin(object):
	"""Allows functions of a subclass that are decorated with 'command'
	to be found with 'get_command'
	"""

	def __init__(self):
		self.commands = dict((c.command_name, c.func)
		                     for c
		                     in (getattr(self, attr_name)
		                         for attr_name
		                         in dir(self))
		                     if isinstance(c, command))


	def get_command(self, command_name):
		"""Find a command named command_name; returns a function.
		Raises CommandNotFound if the command does not exist.
		"""
		try:
			return self.commands[command_name]
		except KeyError, e:
			raise CommandNotFound(str(e))
		


class command(object):
	"""Decorate a command so that it can be found by CommandRunnerMixn.

	For example:

	@command("test")
	def test(self):
	    return "hi"
	    
	"""

	def __init__(self, command_name):
		self.command_name = command_name


	def __call__(self, *args, **kwargs):
		if not hasattr(self, "func"):
			self.func = args[0]
			return self
		else:
			return self.func(*args, **kwargs)

