from shet.client import ShetClient
import sys
import subprocess

class DpmsClient(ShetClient):
	
	
	def __init__(self, action_path):
		ShetClient.__init__(self)
		
		self.add_action(action_path, self.dpms)
	
	def dpms(self, state):
		subprocess.call(["xset", "dpms", "force", "on" if state else "off"])


if __name__ == "__main__":
	DpmsClient(sys.argv[1]).run()
