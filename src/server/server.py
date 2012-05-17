from twisted.internet.protocol import Factory
from twisted.internet.defer import Deferred

from shet import commands

from shet import ShetProtocol
from shet.command_runner import command

from shet.server import file_system

import uuid

class ShetServerProtocol(ShetProtocol):

	def connectionMade(self):
		self.factory.connections.append(self)
		self.connected = True
		self.on_connection_lost = Deferred()
		self.connection_id = str(uuid.uuid1())

		self.fs_nodes = []
		self.watches = set()

	def connectionLost(self, reason):
		self.factory.connections.remove(self)
		self.connected = False
		
		for watch in self.watches:
			try:
				node = self.factory.fs.get_node(watch)
				node.ignore(self)
			except KeyError:
				pass
		
		for node in self.fs_nodes:
			node.delete()

	@command(commands.ping)
	def cmd_ping(self, *args):
		return args

	@command(commands.register)
	def cmd_register(self, connection_id):
		"""Set the connection id of this connection. This closes all other
		connections with the same id, so it must be unique.
		"""
		self.factory.disconnect_id(connection_id)
		self.connection_id = connection_id

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
		self.fs_nodes.remove(node)

	@command(commands.get)
	def cmd_get(self, path):
		node = self.factory.fs.get_node(path)
		return node.get()

	@command(commands.set)
	def cmd_set(self, path, value):
		node = self.factory.fs.get_node(path)
		return node.set(value)

	@command(commands.mkvar)
	def cmd_mkvar(self, path):
		self.fs_nodes.append(file_system.Variable(self.factory.fs,
		                                          path,
		                                          self))

	def update_watches(self):
		"""Watch all events in self.watches.
		"""
		for event in self.watches:
			try:
				node = self.factory.fs.get_node(event)
				node.watch(self)
			except KeyError:
				pass
	
	@command(commands.mkevent)
	def cmd_mkevent(self, path):
		self.fs_nodes.append(file_system.Event(self.factory.fs,
		                                       path,
		                                       self))
		for conn in self.factory.connections:
			conn.update_watches()

	@command(commands.rmevent)
	def cmd_rmevent(self, path):
		node = self.factory.fs.get_node(path)
		assert node.owner == self
		node.delete()
		self.fs_nodes.remove(node)

	@command(commands._raise)
	def cmd_raise(self, path, *args):
		node = self.factory.fs.get_node(path)
		node._raise(*args)

	@command(commands.watch)
	def cmd_watch(self, path):
		self.watches.add(path)
		try:
			node = self.factory.fs.get_node(path)
			node.watch(self)
		except KeyError:
			pass

	@command(commands.ignore)
	def cmd_ignore(self, path):
		self.watches.remove(path)
		try:
			node = self.factory.fs.get_node(path)
			node.ignore(self)
		except KeyError:
			pass

	@command(commands.mkaction)
	def cmd_mkaction(self, path):
		self.fs_nodes.append(file_system.Action(self.factory.fs,
		                                        path,
		                                        self))
	@command(commands.rmaction)
	def cmd_rmaction(self, path):
		node = self.factory.fs.get_node(path)
		assert node.owner == self
		node.delete()
		self.fs_nodes.remove(node)

	@command(commands.call)
	def cmd_call(self, path, *args):
		node = self.factory.fs.get_node(path)
		return node.call(*args)

		


	def send_get(self, path):
		return self.send_command_with_callback(commands.getprop, path)

	def send_set(self, path, value):
		return self.send_command_with_callback(commands.setprop, path, value)

	def send_event(self, path, *args):
		return self.send_command_with_callback(commands.event, path, *args)

	def send_eventcreated(self, path):
		return self.send_command_with_callback(commands.eventcreated, path)
	
	def send_eventdeleted(self, path):
		return self.send_command_with_callback(commands.eventdeleted, path)

	def send_docall(self, path, *args):
		return self.send_command_with_callback(commands.docall, path, *args)


class ShetServerFactory(Factory):
	protocol = ShetServerProtocol

	def __init__(self):
		self.connections = []
		self.fs = file_system.FileSystem()

	def disconnect_id(self, connection_id):
		"""Close all connections with this connection id."""
		for connection in self.connections:
			if connection.connection_id == connection_id:
				connection.transport.loseConnection()
