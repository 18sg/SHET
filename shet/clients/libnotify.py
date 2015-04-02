from shet.client import ShetClient
import pynotify
import sys


class NotifyClient(ShetClient):

	def __init__(self, action):
		ShetClient.__init__(self)
		pynotify.init("SHET")
		self.add_action(action, self.notify)
	
	
	def notify(self, message, title="SHET", expire=True):
		n = pynotify.Notification(title, message)
		n.set_timeout(pynotify.EXPIRES_DEFAULT if expire
		              else pynotify.EXPIRES_NEVER)
		n.show()



if __name__ == "__main__":
	NotifyClient(sys.argv[1]).run()
