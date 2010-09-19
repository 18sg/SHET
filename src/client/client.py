from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from shet import commands
from shet import ShetProtocol
from shet.command_runner import command
import os.path
from types import MethodType


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



class ShetClientProtocol(ShetProtocol):
	"""The low-level SHET client protocol.
	This must be used with the ShetClient as a factory - use that to
	implement clients.
	"""
	def connectionMade(self):
		"""Set up the connection - initialise all properties, events etc.
		and send all queued items.
		"""
		self.factory.resetDelay()
		self.factory.client = self
		self.factory.on_connect()
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
		self.factory.client = None
		self.factory.on_disconnect()

	# Lots of boring code.

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

	@command(commands.getprop)
	def cmd_getprop(self, path):
		return self.factory._get_property(path)

	@command(commands.setprop)
	def cmd_setprop(self, path, value):
		return self.factory._set_property(path, value)

	@command(commands.event)
	def cmd_event(self, path, *args):
		self.factory.watched_events[path][0](*args)

	@command(commands.eventdeleted)
	def cmd_eventdeleted(self, path):
		self.factory.watched_events[path][1]()

	@command(commands.docall)
	def cmd_docall(self, path, *args):
		return self.factory.actions[path].call(*args)



class ShetClient(ReconnectingClientFactory):
	"""A SHET client.
	
	Subclass this to add functionality, or possibly use it as-is.
	"""
	protocol = ShetClientProtocol
	
	root = '/'
	
	def __init__(self):
		self.properties = {}
		self.events = {}
		self.watched_events = {}
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
				self.add_property(name, 
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
		for event in self.watched_events.values():
			self.unwatch_event(event)
	
	
	def relative_path(self, path):
		if path.startswith('/'):
			return path
		else:
			return os.path.join(self.root, path)


	def add_property(self, path, set_callback, get_callback):
		"""Create a property.
		@param path         The path of the property.
		@param set_callback Function called with a single argument to
		                    set the property.
				    May return a Deferred or any value.
		@param get_callback Function called with no args to get 
		                    the resending
		@return Object representing the property.
		        Pass to remove_property() to remove.
		"""
		path = self.relative_path(path)
		prop = Property(path, set_callback, get_callback)
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
		
	
	def watch_event(self, path, callback, delete_callback=lambda:None):
		"""Watch an event on the server.
		@param path Path to the event.
		@param callback Called when the event is raised.
		@param delete_callback Called if the event is deleted.
		@return An object that can be passed to unwatch_event()
		        to stop watching this event.
		"""
		path = self.relative_path(path)
		self.watched_events[path] = (callback, delete_callback)
		if self.client is not None:
			self.client.send_watch(path)		
		return path
	
	def wait_for(self, path):
		"""Wait for an event to fire on the server.
		@param path Path to the event.
		@return A deferred that will be called on the event being fired,
		        or errorred if the event is deleted.
		"""
		d = Deferred()
		event = self.watch_event(path, None, None)
		
		def callback(*args):
			d.callback(args)
			self.unwatch_event(event)
			
		def delete_callback(*args):
			d.errback(args)
			
		self.watched_events[event] = (callback, delete_callback)
		return d

	def unwatch_event(self, event):
		"""Stop watching an event.
		@param event an object returned from watch_event().
		"""
		del self.watched_events[event]
		if self.client is not None:
			self.client.send_ignore(event)
			

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


	def install(self, address, port=11235):
		"""Install this instance into the twisted reactor.
		Use this if you want to run some other service in parallel.
		@param address address to connect to.
		@param port the port to use.
		"""
		reactor.connectTCP(address, port, self)

	def run(self, address, port=11235):
		"""Run this instance of the client.
		This will not return until stop() is called.
		
		nb: This calls twisted.internet.reactor.run().
		@param address address to connect to.
		@param port the port to use.
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


class Action(Node):

	def __init__(self, path, callback):
		self.path = path
		self.callback = callback

	def call(self, *args):
		return self.callback(*args)
