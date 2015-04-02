from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from shet import commands
from shet import ShetProtocol
from shet.command_runner import command
from shet import path as shetpath
import os
from types import MethodType
import collections
import uuid


class Decorator(object):
	func_name = "f"
	
	def __init__(self, f):
		self.has_func = not isinstance(f, basestring)
		if self.has_func:
			self.name = None
			setattr(self, self.func_name, f)
		else:
			self.f = None
			self.name = f
	
	def __call__(self, *args, **kwargs):
		if self.has_func:
			return getattr(self, self.func_name)(*args, **kwargs)
		else:
			setattr(self, self.func_name, args[0])
			self.has_func = False
			return self
		
	
class shet_action(Decorator):
	pass

class shet_property(Decorator):
	func_name = "get"
	def __init__(self, f):
		Decorator.__init__(self, f)
		self.set_f = None
	
	def set(self, f):
		self.set_f = f
		return f


class PingingShetProtocol(ShetProtocol):
	"""A SHET protocol that pings the server every factory.ping_interval seconds.
	If the last ping does not return by the time the next one is scheduled, the
	connection is dropped.
	"""

	def connectionMade(self):
		# Make do_ping think it was successfull the last time the first time it is
		# called.
		self.ping_returned = True
		self.ping_timer = reactor.callLater(self.factory.ping_interval, self.do_ping)

	def connectionLost(self, reason):
		if self.ping_timer.active():
			self.ping_timer.cancel()

	def on_ping_return(self, *args):
		"""Called when a ping is returned from the server."""
		self.ping_returned = True

	def do_ping(self):
		"""Check the status of the last ping. If it returned, ping again and set up
		another delayed call. If it didn't return, drop the connection.
		"""
		if self.ping_returned:
			d = self.send_ping()
			d.addCallbacks(self.on_ping_return, self.on_ping_return)
			self.ping_timer = reactor.callLater(self.factory.ping_interval, self.do_ping)
		else:
			self.transport.loseConnection()

	def send_ping(self, *args):
		"""Send a ping to the server, returning a deferred."""
		return self.send_command_with_callback(commands.ping, *args)


class ShetClientProtocol(PingingShetProtocol):
	"""The low-level SHET client protocol.
	This must be used with the ShetClient as a factory - use that to
	implement clients.
	"""
	def connectionMade(self):
		"""Set up the connection - initialise all properties, events etc.
		and send all queued items.
		"""
		self.factory.resetDelay()
		PingingShetProtocol.connectionMade(self)
		self.factory.client = self
		self.factory.on_connect()
		
		self.send_register(self.factory.connection_id)
		
		# Set up properties
		for prop_path in self.factory.properties:
			self.send_mkprop(prop_path)

		# Set up events
		for event_path in self.factory.events:
			self.send_mkevent(event_path)

		# Set up watched events.
		for event_path in self.factory.watched_events:
			self.send_watch(event_path)

		# Set up actions.
		for event_path in self.factory.actions:
			self.send_mkaction(event_path)

		# Perform any queued get operations.
		for path, d in self.factory.get_queue:
			self.send_get(path).chainDeferred(d)
		self.factory.get_queue = []

		# Perform any queued set operations.
		for path, value, d in self.factory.set_queue:
			self.send_set(path, value).chainDeferred(d)
		self.factory.set_queue = []

		# Perform any queued raise operations.
		for path, args, d in self.factory.raise_queue:
			self.send_raise(path, *args).chainDeferred(d)
		self.factory.raise_queue = []

		# Perform any queued call operations.
		for path, args, d in self.factory.call_queue:
			self.send_call(path, *args).chainDeferred(d)
		self.factory.call_queue = []


	def connectionLost(self, reason):
		"""Called on disconnect."""
		PingingShetProtocol.connectionLost(self, reason)
		self.factory.client = None
		self.factory.on_disconnect()

	# Lots of boring code.

	def send_register(self, connection_id):
		return self.send_command_with_callback(commands.register, connection_id)

	# Properties
	def send_mkprop(self, path):
		return self.send_command_with_callback(commands.mkprop, path)
	def send_rmprop(self, path):
		return self.send_command_with_callback(commands.rmprop, path)

	def send_get(self, path):
		return self.send_command_with_callback(commands.get, path)
	def send_set(self, path, value):
		return self.send_command_with_callback(commands.set, path, value)


	# Events
	def send_mkevent(self, path):
		return self.send_command_with_callback(commands.mkevent, path)
	def send_rmevent(self, path):
		return self.send_command_with_callback(commands.rmevent, path)
	def send_raise(self, path, *args):
		return self.send_command_with_callback(commands._raise, 
						       path, *args)

	def send_watch(self, path):
		return self.send_command_with_callback(commands.watch, path)
	def send_ignore(self, path):
		return self.send_command_with_callback(commands.ignore, path)


	# Actions
	def send_mkaction(self, path):
		return self.send_command_with_callback(commands.mkaction, path)
	def send_rmaction(self, path):
		return self.send_command_with_callback(commands.rmaction, path)

	def send_call(self, path, *args):
		return self.send_command_with_callback(commands.call, path, *args)

	@command(commands.ping)
	def cmd_ping(self, *args):
		return args

	@command(commands.getprop)
	def cmd_getprop(self, path):
		return self.factory._get_property(path)

	@command(commands.setprop)
	def cmd_setprop(self, path, value):
		return self.factory._set_property(path, value)

	@command(commands.event)
	def cmd_event(self, path, *args):
		# Make a copy of the dict so that if the callbacks watch events they
		# aren't immediately called.
		for event in list(self.factory.watched_events[path]):
			if event.callback is not None:
				event.callback(*args)

	@command(commands.eventdeleted)
	def cmd_eventdeleted(self, path):
		for event in list(self.factory.watched_events[path]):
			if event.delete_callback is not None:
				event.delete_callback()

	@command(commands.eventcreated)
	def cmd_eventcreated(self, path):
		for event in list(self.factory.watched_events[path]):
			if event.create_callback is not None:
				event.create_callback()

	@command(commands.docall)
	def cmd_docall(self, path, *args):
		return self.factory.actions[path].call(*args)



class ShetClient(ReconnectingClientFactory):
	"""A SHET client.
	
	Subclass this to add functionality, or possibly use it as-is.
	"""
	protocol = ShetClientProtocol
	
	root = '/'
	
	# Maximum reconnection delay.
	maxDelay = 5
	
	# Time between sending pings to the server.
	ping_interval = 30
	
	def __init__(self):
		self.connection_id = str(uuid.uuid1())
		
		self.properties = {}
		self.events = {}
		self.watched_events = collections.defaultdict(list)
		self.actions = {}
		self.get_queue = []
		self.set_queue = []
		self.raise_queue = []
		self.call_queue = []
		self.client = None
		
		for name in dir(self):
			attr = getattr(self, name)
			if isinstance(attr, shet_action):
				action_name = attr.name or name
				self.add_action(action_name, MethodType(attr.f, self, self.__class__))
				setattr(self, name, MethodType(attr.f, self, self.__class__))
			elif isinstance(attr, shet_property):
				prop_name = attr.name or name
				self.add_property(prop_name, 
				                   MethodType(attr.get, self, self.__class__),
				                   MethodType(attr.set_f, self, self.__class__))
				setattr(self, name, MethodType(attr.get, self, self.__class__),)


	def on_connect(self):
		"""Called when the client connects to the server.
		"""
		pass

	def on_disconnect(self):
		"""Called when the client disconnects from the server.
		"""
	
	
	def reset(self):
		"""Unregister everything!
		"""
		
		for prop in self.properties.values():
			self.remove_property(prop)
		for event in self.events.values():
			self.remove_event(event)
		for action in self.actions.values():
			self.remove_action(action)
		for event in self.watched_events:
			for watch in event:
				self.unwatch_event(watch)
	
	
	def relative_path(self, path):
		if path.startswith('/'):
			return path
		else:
			return shetpath.join(self.root, path)


	def add_property(self, path, get_callback, set_callback):
		"""Create a property.
		@param path         The path of the property.
		@param get_callback Function called with no args to get 
		                    the value of the property.
		@param set_callback Function called with a single argument to
		                    set the property.
		@return Object representing the property.
		        Pass to remove_property() to remove.
		"""
		path = self.relative_path(path)
		prop = Property(path, get_callback, set_callback)
		self.properties[path] = prop
		if self.client is not None:
			self.client.send_mkprop(path)
		return prop
		
	def remove_property(self, prop):
		"""Remove a property.
		@param prop Object returned from add_property().
		"""
		del self.properties[prop.path]
		if self.client is not None:
			self.client.send_rmprop(prop.path)
		

	def add_event(self, path):
		"""Create an event.
		@param path The path to the event.
		@return An Event object.
		        Pass this to remove_event() to remove the event.
			Call this like a function to raise the event.
		"""
		path = self.relative_path(path)
		def _raise(*args):
			return self._raise(path, *args)
		event = Event(path, _raise)
		self.events[path] = event
		if self.client is not None:
			self.client.send_mkevent(path)
		return event

	def remove_event(self, event):
		"""Remove an event.
		@param event Object returned from add_event().
		"""
		del self.events[event.path]
		if self.client is not None:
			self.client.send_rmevent(event.path)
		
	
	def watch_event(self, path, callback, create_callback=None, delete_callback=None):
		"""Watch an event on the server.
		@param path Path to the event.
		@param callback Called when the event is raised.
		@param delete_callback Called if the event is deleted.
		@return An object that can be passed to unwatch_event()
		        to stop watching this event.
		"""
		path = self.relative_path(path)
		
		if not self.watched_events[path] and self.client is not None:
				self.client.send_watch(path)
		
		watch = Watch(path, callback, create_callback, delete_callback)
		self.watched_events[path].append(watch)
		return watch
	
	def wait_for(self, path):
		"""Wait for an event to fire on the server.
		@param path Path to the event.
		@return A deferred that will be called on the event being fired.
		"""
		d = Deferred()
		# We can't define the callback function without having the event.
		event = self.watch_event(path, None)
		
		def callback(*args):
			d.callback(args)
			self.unwatch_event(event)
		
		# Inject the callback.
		event.callback = callback
		
		return d

	def unwatch_event(self, event):
		"""Stop watching an event.
		@param event an object returned from watch_event().
		"""
		self.watched_events[event.path].remove(event)
		# TODO: possibly unwatch event.

	def add_action(self, path, callback):
		"""Create an action.
		@param path     Path to the action.
		@param callback Called when the action is called.
		@return An object that can be passed to remove_action()
		        to remove this action.
		"""
		path = self.relative_path(path)
		action = Action(path, callback)
		self.actions[path] = action
		if self.client is not None:
			self.client.send_mkaction(path)
		return action

	def remove_action(self, action):
		"""Remove an action.
		@param action The action to remove, returned from add_action().
		""" 
		del self.actions[action.path]
		if self.client is not None:
			self.client.send_rmaction(action.path)


	def call(self, path, *args):
		"""Call an action on the server.
		@param path Path to the action.
		@param *args the arguments of the action.
		@return The Deferred result of the action.
		"""
		path = self.relative_path(path)
		if self.client is not None:
			return self.client.send_call(path, *args)
		else:
			d = Deferred()
			self.call_queue.append((path, args, d))
			return d


	def get(self, path):
		"""Get a property on the server.
		@param path The path to the property.
		@return The Deferred value of the property.
		"""
		path = self.relative_path(path)
		if self.client is not None:
			return self.client.send_get(path)
		else:
			d = Deferred()
			self.get_queue.append((path, d))
			return d

	def set(self, path, value):
		"""Set a property on the server.
		@param path The path to the property.
		@param value The new value.
		@return Deferred success/failure.
		"""
		path = self.relative_path(path)
		if self.client is not None:
			return self.client.send_set(path, value)
		else:
			d = Deferred()
			self.set_queue.append((path, value, d))
			return d

	def act(self, path, *args):
		"""Either call an action, or set a property.
		If the path starts with "action:", it is called as an action.
		If the path starts with "property:", it is set as a property.
		Otherwise, it is assumed to be an action.
		"""
		if path.startswith("action:"):
			path = path.partition(":")[2].strip()
			self.call(path, *args)
		elif path.startswith("property:"):
			path = path.partition(":")[2].strip()
			self.set(path, *args)
		else:
			self.call(path, *args)

	def _raise(self, path, *args):
		if self.client is not None:
			return self.client.send_raise(path, *args)
		else:
			d = Deferred()
			self.raise_queue.append((path, args, d))
			return d


	def _get_property(self, path):
		return self.properties[path].get()

	def _set_property(self, path, value):
		return self.properties[path].set(value)


	def install(self, address=None, port=None):
		"""Install this instance into the twisted reactor.
		Use this if you want to run some other service in parallel.
		@param address address to connect to; defaults to $SHET_HOST or localhost.
		@param port the port to use; defaults to $SHET_PORT or 11235
		"""
		address = address or os.getenv("SHET_HOST") or "localhost"
		port = int(port or os.getenv("SHET_PORT") or 11235)
		reactor.connectTCP(address, port, self)

	def run(self, address=None, port=None):
		"""Run this instance of the client.
		This will not return until stop() is called.
		
		nb: This calls twisted.internet.reactor.run().
		@param address address to connect to; defaults to $SHET_HOST or localhost.
		@param port the port to use; defaults to $SHET_PORT or 11235
		"""
		self.install(address, port)
		reactor.run()

	def stop(self):
		"""Stop the client.

		nb: This calls twisted.internet.reactor.stop()
		"""
		reactor.stop()



# Internal objects that the client programmer doesn't need to know about.

class Node(object):
	pass


class Property(Node):
	
	def __init__(self, path, get_callback, set_callback):
		self.path = path
		self.get_callback = get_callback
		self.set_callback = set_callback

	def get(self):
		return self.get_callback()

	def set(self, value):
		self.set_callback(value)


class Event(Node):

	def __init__(self, path, raise_callback):
		self.raise_callback = raise_callback
		self.path = path

	def _raise(self, *args):
		self.raise_callback(*args)
	
	__call__ = _raise

class Watch(Node):

	def __init__(self, path, callback, create_callback, delete_callback):
		self.path = path
		self.callback = callback
		self.create_callback = create_callback
		self.delete_callback = delete_callback


class Action(Node):

	def __init__(self, path, callback):
		self.path = path
		self.callback = callback

	def call(self, *args):
		return self.callback(*args)
