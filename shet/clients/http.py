from twisted.web.http import HTTPFactory
from twisted.web.http import HTTPChannel
from twisted.web.http import Request
from twisted.internet import reactor
from shet.client import ShetClient
from shet.sync import make_sync
import json

class MyRequest(Request):
	
	@make_sync
	def process(self):
		self.shet = self.channel.shet
		
		try:
			type = (yield self.shet.call("/meta/type", self.uri))
			if type == "prop":
				if "value" in self.args:
					value = (yield self.shet.set(self.uri, json.loads(self.args["value"][0])))
				else:
					value = (yield self.shet.get(self.uri))
			elif type == "action":
				args = json.loads(self.args["args"][0]) if "args" in self.args else []
				value = (yield self.shet.call(self.uri, *args))
			elif type == "event":
				value = (yield self.shet.wait_for(self.uri))
			else:
				value = None
			self.setResponseCode(200)
			self.write(json.dumps(value))
			self.write('\r\n')
			self.finish()
		except Exception, e:
			self.setResponseCode(500)
			self.write(repr(e))
			self.write("\r\n")
			self.finish()


class MySite(HTTPChannel):
	requestFactory = MyRequest

class MyFactory(HTTPFactory):
	protocol = MySite
	
	def __init__(self, shet):
		self.shet = shet
		HTTPFactory.__init__(self)
	
	def buildProtocol(self, *args, **kwargs):
		p = HTTPFactory.buildProtocol(self, *args, **kwargs)
		p.shet = self.shet
		return p


if __name__ == "__main__":
	shet = ShetClient()
	shet.install()
	reactor.listenTCP(8080, MyFactory(shet))
	reactor.run()
