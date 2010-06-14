from twisted.internet.protocol import Factory
from twisted.internet.defer import Deferred

from shet import commands

from shet import ShetProtocol
from shet.command_runner import command

from shet.server import file_system


class ShetServerProtocol(ShetProtocol):

	def connectionMade(self):
		self.factory.connections.append(self)
		self.connected = True
		self.on_connection_lost = Deferred()

		self.fs_nodes = []

	def connectionLost(self, reason):
		self.factory.connections.remove(self)
		self.connected = False

		for node in self.fs_nodes:
			node.delete()


	@command(commands.mkprop)
	def cmd_mkprop(self, path):
		self.fs_nodes.append(file_system.Property(self.factory.fs,
		                                          path,
		                                          self))

	@command(commands.rmprop)
	def cmd_rmprop(self, path):
		node = self.factory.fs.get_node(path)
		assert node.owner == self
		node.delete()

	@command(commands.get)
	def cmd_get(self, path):
		node = self.factory.fs.get_node(path)
		return node.get()

	@command(commands.set)
	def cmd_set(self, path, value):
		node = self.factory.fs.get_node(path)
		node.set(value)

	@command(commands.mkvar)
	def cmd_mkvar(self, path):
		self.fs_nodes.append(file_system.Variable(self.factory.fs,
		                                          path,
		                                          self))

	@command(commands.mkevent)
	def cmd_mkevent(self, path):
		self.fs_nodes.append(file_system.Event(self.factory.fs,
		                                       path,
		                                       self))

	@command(commands.rmevent)
	def cmd_rmevent(self, path):
		node = self.factory.fs.get_node(path)
		assert node.owner == self
		node.delete()

	@command(commands._raise)
	def cmd_raise(self, path):
		node = self.factory.fs.get_node(path)
		node._raise()

	@command(commands.watch)
	def cmd_watch(self, path):
		node = self.factory.fs.get_node(path)
		node.watch(self)

	@command(commands.ignore)
	def cmd_ignore(self, path):
		node = self.factory.fs.get_node(path)
		node.ignore(self)

	@command(commands.mkaction)
	def cmd_mkaction(self, path):
		self.fs_nodes.append(file_system.Action(self.factory.fs,
		                                        path,
		                                        self))

	@command(commands.call)
	def cmd_call(self, path):
		node = self.factory.fs.get_node(path)
		node.call()

		


	def send_get(self, path):
		return self.send_command_with_callback(commands.getprop, path)

	def send_set(self, path, value):
		return self.send_command_with_callback(commands.setprop, path, value)

	def send_event(self, path):
		return self.send_command_with_callback(commands.event, path)

	def send_eventdeleted(self, path):
		return self.send_command_with_callback(commands.eventdeleted, path)

	def send_docall(self, path):
		return self.send_command_with_callback(commands.docall, path)


class ShetServerFactory(Factory):
	protocol = ShetServerProtocol

	def __init__(self):
		self.connections = []
		self.fs = file_system.FileSystem()
