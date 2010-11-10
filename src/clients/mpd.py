from shet.client import ShetClient
from twisted.internet import threads
import sys
import subprocess


class MpdClient(ShetClient):
	
	def __init__(self, dir):
		self.root = dir
		ShetClient.__init__(self)
		
		commands = """next prev play toggle stop clear seek move
		              volume repeat random single consume findadd""".split()
		
		# Because closures in python are... a bit nutty.
		def make_command(name):
			def f(*args):
				return threads.deferToThread(subprocess.call,
				                             ["mpc", name] + map(str, args))
			return f
		
		for command in commands:
			self.add_action(command, make_command(command))


if __name__ == "__main__":
	MpdClient(sys.argv[1]).run()
