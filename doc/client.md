Writing a SHET Client
=====================

All clients will probably contain something like this:

	from shet.client import ShetClient

	# Subclass ShetClient.
	class MyClient(ShetClient):
		
		# All nodes created by this client will be relative to this directory,
		# unless they begin with a '/'.
		root = "/test/"
		
		def __init__(self, dir):
			# Make sure you initialise the shet client in your constructor.
			ShetClient.__init__(self)

	# Instantiate and run the client.
	if __name__ == "__main__":
		MyClient().run()


Actions
-------

### Creating

There are two ways of creating actions; either call `self.add_action(path, callback)`:

	self.add_action("test_action", self.on_test_action)
	
	...
	
	def on_test_action(self):
		print "Test!"

, or use the `shet_action` decorator:

	@shet_action("test_action")
	def on_test_action(self):
		print "Test!"

Alternatively, you can use this form, which uses the function name as the action name.

	@shet_action
	def test_action(self):
		print "Test!"

### Calling

To call an action, use `self.call(path, *args)`. This returns a deferred containing the value; see the [Deferred Values](#deferred) section for more info.

### Deleting

`add_action` returns an object that can be passed to `self.remove_action(obj)` to remove it from SHET.


Events
------

### Creating

To add an event, call `self.add_event(path)`. This returns an object that can be called (with arguments) to raise the event:

	self.test_event = self.add_event("test_event")
	
	...
	
	self.test_event(42)

### Deleting

Call `self.remove_event` on the event object to remove an event.

### Watching

To watch an external event, call `self.watch_event(path, callback)`:

	self.watch_event("test_event", self.on_test_event)
	
	...
	
	def on_test_event(self, x):
		print "Test: %s!" % x

Properties
----------

### Creating

To add a property, call `self.add_property(path, set_callback, get_callback)`:

	self.add_property("x", self.set_x, self.get_x)
	
	...
	
	def get_x(self):
		return self.x
	
	def set_x(self, x):
		self.x = x

### Deleting

As with other node types, call `remove_property` with the return value of `add_property`.

### Setting and Getting

External properties can be set with `self.set(path, value)`, and got with `self.get(path)`. `get` returns a deferred containing the value; see the [Deferred Values](#deferred) section for more info.

<a name="deferred">

Deferred Values
---------------

</a>
Beware that `get` and `call` return deferreds containing the value. To deal with this, you can write something like this:

	def add_one_to_x(self):
		
		def on_x_value(self, value):
			self.set("x", value + 1)
		
		self.get("x").addCallback(on_x_value)

That's a lot of work to increment a value. Luckily, there's an alternative:

	from shet.sync import make_sync
	
	@make_sync
	def add_one_to_x(self):
		self.set("x", (yield self.get("x")) + 1)

This turns your function into a [coroutine](http://www.python.org/dev/peps/pep-0342/) using Python's generator syntax. It's hairy, but it works surprisingly well. To return a value from a function written like this, yield it and exit as normal. Functions written in this style return immediately with a deferred.

See the twisted [Deferred](http://twistedmatrix.com/documents/current/core/howto/defer.html) documentation for more info.

Notes
-----

- The decorators are in the `shet.client` module.
- Clients automatically reconnect (and restore all nodes) if they are disconnected.
- Events by default re-watch if they disappear.
- An `on_event` decorator is in the feature queue.
