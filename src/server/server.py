from twisted.internet.protocol import Factory

import commands
from id_generator import IdGeneratorMixin

from shet import ShetProtocol
from shet.command_runner import command



class ShetServerProtocol(ShetProtocol):

	def connectionMade(self):
		self.factory.connections.append(self)
		self.connected = True

	def connectionLost(self, reason):
		self.factory.connections.remove(self)
		self.connected = False


	def test_cb(self, msg):
		print msg
		return "you said: %s" % msg

	@command("test")
	def cmd_test(self):
		d = self.send_command_with_callback("foo", "hello")
		return d.addCallback(self.test_cb)

	@command("test_block")
	def cmd_test_blocking(self):
		return "See?"
		

	@command("test_error")
	def cmd_test_error(self):
		raise Exception("Oh Shit!")



class ShetServerFactory(Factory):
	protocol = ShetServerProtocol

	def __init__(self):
		self.connections = []
