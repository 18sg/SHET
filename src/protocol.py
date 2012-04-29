from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred, maybeDeferred

import json
import traceback

from shet import IdGeneratorMixin
from shet.command_runner import CommandRunnerMixin, command
from shet.error import serialize_error
import commands


class ShetProtocol(LineReceiver,
                   IdGeneratorMixin,
                   CommandRunnerMixin):

	MAX_LENGTH = 1048576

	def __init__(self, *args, **kwargs):
		CommandRunnerMixin.__init__(self)
		self.waiting_for_return = {}


	def lineReceived(self, line):
		command = json.loads(line)

		try:
			return_id = command[0]
			command_name = command[1]
			args = command[2:]

			if command_name == commands._return:
				self.cmd_return(return_id, *args)
			else:
				d = maybeDeferred(self.get_command(command_name), self, *args)
				d.addCallback(self.command_complete, return_id)
				d.addErrback(self.command_fail, return_id)

		except Exception, e:
			self.send_command(return_id, commands._return, 1, serialize_error(e))


	def command_complete(self, retval, return_id):
		self.send_command(return_id, commands._return, 0, retval)

	def command_fail(self, e, return_id):
		e.printTraceback()
		self.send_command(return_id, commands._return, 1, serialize_error(e))
		

	def send_command(self, return_id, name, *args):
		if return_id is None:
			return_id = self.get_id()
		
		command = (return_id, name) + args
		self.sendLine(json.dumps(command))


	def send_command_with_callback(self, name, *args):
		return_id = self.get_id()
		
		self.send_command(return_id, name, *args)

		d = Deferred()
		self.waiting_for_return[return_id] = d

		return d


	def cmd_return(self, return_id, status, retval):
		d = self.waiting_for_return[return_id]
		del self.waiting_for_return[return_id]

		if status == 0:
			d.callback(retval)
		else:
			d.errback(retval)
