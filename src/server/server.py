from twisted.internet.protocol import Factory

import commands
from id_generator import IdGeneratorMixin

from shet import ShetProtocol

class ShetServerProtocol(ShetProtocol):
	def test_cb(self, msg):
		print msg
		return "you said: %s" % msg

	def cmd_test(self):
		d = self.send_command_with_callback("foo", "hello")
		return d.addCallback(self.test_cb)
		


	def cmd_test_error(self):
		raise Exception("Oh Shit!")


	commands = {"test" : cmd_test,
	            "test_error" : cmd_test_error}


class ShetServerFactory(Factory):
	protocol = ShetServerProtocol
