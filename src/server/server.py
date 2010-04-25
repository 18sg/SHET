from twisted.internet.protocol import Factory
from twisted.internet.defer import Deferred

import commands

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




	def send_get(self, path):
		return self.send_command_with_callback(commands.getprop, path)

	def send_set(self, path, value):
		return self.send_command_with_callback(commands.setprop, path, value)


class ShetServerFactory(Factory):
	protocol = ShetServerProtocol

	def __init__(self):
		self.connections = []
		self.fs = file_system.FileSystem()
