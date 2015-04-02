from shet.client import ShetClient, shet_action
from twisted.internet import reactor
import collections
import functools


class State(object):
	
	def __init__(self, name):
		self.name = name
		self.active = False
		self.properties = []
		self.stack = []
	
	def bind(self, parent):
		assert not hasattr(self, "parent"), "You should only bind a State to one parent."
		self.parent = parent
	
	def add_property(self, property):
		self.properties.append(property)
		property.bind(self)
	
	def activate(self):
		changed = not self.active
		self.active = True
		
		print "\t %s" % self
		
		for property in self.properties:
			if property.always or changed:
				property.on_activate()
	
	def deactivate(self):
		changed = self.active
		self.active = False
		
		print "\t %s" % self
		
		for property in self.properties:
			if property.always or changed:
				property.on_deactivate()
	
	def push(self):
		self.stack.append(self.active)
	
	def pop(self):
		try:
			active = self.stack.pop()
		except:
			return
		if active:
			self.activate()
		else:
			self.deactivate()
	
	def transform_to(self, new_state):
		print "%s -> %s" % (self.name, new_state.name)
		# if self.active:
		self.deactivate()
		new_state.activate()
	
	def __repr__(self):
		return "%s(%s, %s)" % ( self.__class__.__name__
		                      , self.name
		                      , self.active
		                      )



class StateProperty(object):
	
	always = True
	
	def bind(self, state):
		assert not hasattr(self, "state"), "You should only bind a StateProperty to one state."
		self.state = state
	
	def on_activate(self):
		pass
		
	def on_deactivate(self):
		pass



class Timeout(StateProperty):
	
	def __init__(self, timeout, next_state, always=True):
		StateProperty.__init__(self)
		self.timeout = timeout
		self.next_state = next_state
		self.timer = None
		self.always = always
	
	def on_activate(self):
		if self.timer is None or not self.timer.active():
			self.timer = reactor.callLater(self.timeout, self.on_timer)
		else:
			self.timer.reset(self.timeout)
	
	def on_timer(self):
		self.state.transform_to(self.next_state)



class RaiseOnActivate(StateProperty):
	
	def __init__(self, property, value=None, always=False):
		self.property = property
		self.value = value
		self.always = always
	
	def on_activate(self):
		self.property(self.value)



class CallOnActivate(StateProperty):
	
	def __init__(self, shet_client, action, value=None, always=False):
		self.shet_client = shet_client
		self.action = action
		self.value = value
		self.always = always
	
	def on_activate(self):
		self.shet_client.call(self.action, self.value)



class SetOnActivate(StateProperty):
	
	def __init__(self, shet_client, action, value=None, always=False):
		self.shet_client = shet_client
		self.action = action
		self.value = value
		self.always = always
	
	def on_activate(self):
		self.shet_client.set(self.action, self.value)



class PyCallOnActivate(StateProperty):
	
	def __init__(self, callback, always=False, *args, **kwargs):
		self.callback = callback
		self.always = always
		self.args = args
		self.kwargs = kwargs
	
	def on_activate(self):
		self.callback(*self.args, **self.kwargs)



class TransformOnEvent(StateProperty):
	
	def __init__(self, shet_client, event_name, next_state):
		self.shet_client = shet_client
		self.event_name = event_name
		self.next_state = next_state
		self.watching = False
	
	def on_activate(self):
		if not self.watching:
			self.watch = self.shet_client.watch_event(self.event_name, self.on_event)
			self.watching = True
	
	def on_deactivate(self):
		if self.watching:
			self.shet_client.unwatch_event(self.watch)
			self.watching = False
		
	def on_event(self):
		self.state.transform_to(self.next_state)



class TransformAlwaysOnEvent(StateProperty):
	
	def __init__(self, shet_client, event_name, next_state):
		self.shet_client = shet_client
		self.event_name = event_name
		self.next_state = next_state
		self.watch = self.shet_client.watch_event(self.event_name, self.on_event)
	
	def on_event(self):
		self.state.transform_to(self.next_state)



class StateMachine(object):
	pass

class StateMixIn(object):
	def __init__(self):
		self.states = collections.defaultdict(list)
	
	def push_shet_state(self, prop_name):
		self.get(prop_name).addCallback(self.states[prop_name].append)
	
	def pop_shet_state(self, prop_name):
		try:
			self.set(prop_name, self.states[prop_name].pop())
		except:
			pass


class LightingMixIn(object):
	
	def __init__(self):
		self.lights = {}
	
	def change_on_event(self, event, *states):
		states = list(states)
		for state_a, state_b in zip(states, states[1:] + [states[0]]):
			state_a.add_property(TransformOnEvent(self, event, state_b))
	
	def add_controller(self, states, values, controller, *args, **kwarks):
		for state, value in zip(states, values):
			state.add_property(controller(*list(args) + [value], **kwarks))
	
	def setup_timed_light(self, name, light_prop, pir, timeout, always=False):
		light = SwitchStates(State("%s_off" % name), State("%s_on" % name))
		
		self.add_controller(light, [0, 1], SetOnActivate, self, light_prop, always=False)
		light.on.add_property(Timeout(timeout, light.off))
		light.off.add_property(TransformAlwaysOnEvent(self, pir, light.on))
		light.off.activate()
	
	def add_link(self, link, root=""):
		self.add_action("/tom/%s" % link, self.add_event("/tom/on_%s" % link))
	
	def link_event(self, event, action):
		self.watch_event(event, functools.partial(self.call, action))
	
	def push_state(self):
		for light in self.lights.itervalues():
			light.on.push()
			light.off.push()
	
	def pop_state(self):
		for light in self.lights.itervalues():
			light.on.pop()
			light.off.pop()
	
	def all_on(self, *args):
		for light in self.lights.itervalues():
			light.off.transform_to(light.on)
	
	def all_off(self, *args):
		for light in self.lights.itervalues():
			light.on.transform_to(light.off)



SwitchStates = collections.namedtuple("SwitchStates", "off on")
BoolStates = collections.namedtuple("BoolStates", "false true")



class TestStateMachine(ShetClient, StateMachine, LightingMixIn, StateMixIn):
	
	def __init__(self):
		ShetClient.__init__(self)
		LightingMixIn.__init__(self)
		StateMixIn.__init__(self)
		
		self.setup_timed_light("hall", "/tom/servo", "/tom/pir_landing", 30)
		self.setup_timed_light("bog", "/jonathan/arduino/bogvo", "/jonathan/arduino/pir", 120)
		
		for link in "all_off all_on exit enter".split():
			self.add_link(link, "/tom/")
		
		for name in "desk bedside reading".split():
			self.setup_tomn_light(name)
		
		self.watch_event("/tom/on_all_on", self.all_on)
		self.watch_event("/tom/on_all_off", self.all_off)
		self.watch_event("/tom/switch_a", self.on_switch_a)
		self.watch_event("/tom/switch_b", self.on_switch_b)
		
		self.is_in = BoolStates(State("out"), State("in"))
		self.going_out = State("going_out")
		
		self.is_in.false.add_property(TransformOnEvent(self, "/tom/pir", self.is_in.true))
		self.is_in.true.add_property(TransformOnEvent(self, "/tom/on_exit", self.going_out))
		self.going_out.add_property(Timeout(10, self.is_in.false))
		
		self.is_in.false.add_property(PyCallOnActivate(self.push_state))
		self.is_in.false.add_property(CallOnActivate(self, "/tom/all_off"))
		self.is_in.true.add_property(PyCallOnActivate(self.pop_state))
		self.is_in.true.add_property(CallOnActivate(self, "/tom/dpms", True))
		
		self.going_out.add_property(CallOnActivate(self, "/tom/dpms", False))
		self.going_out.add_property(PyCallOnActivate(self.push_shet_state, self, "/tom/mpd/playing"))
		self.going_out.add_property(SetOnActivate(self, "/tom/mpd/playing", False))
		self.is_in.true.add_property(PyCallOnActivate(self.pop_shet_state, self, "/tom/mpd/playing"))
		
		self.is_in.true.activate()
	
	def setup_tomn_light(self, name):
		self.add_link("toggle_%s" % name, "/tom/")
		
		
		light = SwitchStates(State("%s_off" % name), State("%s_on" % name))
		
		self.add_controller(light, [0, 1], CallOnActivate, self, "/tom/%s" % name)
		self.change_on_event("/tom/on_toggle_%s" % name, *light)
		light.on.activate()
		
		self.lights[name] = light
	
	def on_switch_a(self, no):
		actions = {1: "/tom/xine/pause",
		           2: "/tom/all_off",
		           3: "/tom/toggle_bedside",
		           4: "/tom/toggle_reading",
		           5: "/tom/toggle_desk" }
		self.call(actions[no])
	
	def on_switch_b(self, no):
		actions = {1: "/tom/exit",
		           2: "/tom/all_on",
		           3: "/tom/toggle_bedside",
		           4: "/tom/toggle_reading",
		           5: "/tom/toggle_desk" }
		self.call(actions[no])



if __name__ == "__main__":
	TestStateMachine().run()
