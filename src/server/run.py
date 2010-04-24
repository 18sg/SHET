from server import ShetFactory
from twisted.internet import reactor


def main():
	port = 11235

	reactor.listenTCP(port, ShetFactory())
	print "Running on port %i..." % port
	reactor.run()


if __name__ == "__main__":
	main()