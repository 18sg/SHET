from shet import path as shetpath
from collections import defaultdict

def is_meta(path):
	return path.startswith("/meta/")

class DirectoryTree(dict):
	
	type = "dir"
	
	def __init__(self, parent=None):
		dict.__init__(self)
		self.parent = parent
	
	def get_add(self, key, add=True):
		if add and key not in self:
			self[key] = DirectoryTree(self)
		
		return self[key]
	
	def __delitem__(self, key):
		dict.__delitem__(self, key)
		
		if not self and self.parent is not None:
			for key, value in self.parent.iteritems():
				if value == self:
					del self.parent[key]
					break

class FileSystem(object):
	
	def __init__(self):
		self.root = DirectoryTree()


	def split_path(self, path):
		return filter(len, path.split('/'))

	def join_path(self, path):
		return '/'.join(path)


	def get_node(self, path):
		"""Get a node with a given path."""
		current = self.root
		for part in self.split_path(path):
			if not isinstance(current, DirectoryTree):
				raise Exception("Cannot descend into %s." % current.type)
			
			current = current[part]
		return current
	
	def get_dir(self, path):
		"""Get a directory with a given path.
		This possibly adds new directories, so it is important that something is
		put into it so we don't leave empty directories around.
		"""
		current = self.root
		for part in self.split_path(path):
			if not isinstance(current, DirectoryTree):
				raise Exception("Cannot descend into %s." % current.type)
			
			current = current.get_add(part)
		return current

	
	def simplify_node(self, node, recursive=True):
		if isinstance(node, DirectoryTree):
			return dict((key, self.simplify_node(value) 
			                  if recursive 
			                  else value.type)
			            for (key, value)
			            in node.iteritems())
		else:
			return node.type


	def list_dir(self, path='/', recursive=True):
		return self.simplify_node(self.get_node(path), recursive)


	def list_full_paths(self, path='/'):
		path = path.rstrip('/')
		node = self.get_node(path)

		if not isinstance(node, DirectoryTree):
			return
		else:
			for name, sub_node in node.iteritems():
				if isinstance(sub_node, DirectoryTree):
					for sub_path in self.list_full_paths(shetpath.join(path,
					                                                  name)):
						yield shetpath.join(name,
						                   sub_path)
				else:
					yield name
				
			
	def add(self, full_path, node):
		path, name = shetpath.split(full_path)
		
		assert name, Exception("Must specify a file.")
		
		directory = self.get_dir(path)
		assert name not in directory, Exception(
			"Path %s already exists." % full_path)
		directory[name] = node
		self.on_change("add", full_path)


	def remove(self, path):
		head, tail = shetpath.split(path)
		
		del self.get_node(head)[tail]
		self.on_change("remove", path)
	
	def on_change(self, action, path):
		pass
		
		
class Node(object):

	def __init__(self, fs, path, owner):
		self.fs = fs
		self.path = path
		self.owner = owner
		self.fs.add(path, self)

	def delete(self, reason=None):
		self.fs.remove(self.path)



class Property(Node):
	type = "prop"

	def get(self):
		
		def on_value(value):
			self.fs.on_get(self.path, value)
			return value
		
		d = self.owner.send_get(self.path)
		
		if not is_meta(self.path):
			d.addCallback(on_value)
		
		return d

	def set(self, value):
		if not is_meta(self.path):
			self.fs.on_set(self.path, value)
		
		return self.owner.send_set(self.path, value)

		
class Variable(Property):

	value = None

	def get(self):
		return self.value

	def set(self, value):
		self.value = value


class Event(Node):
	type = "event"

	def __init__(self, *args, **kwargs):
		Node.__init__(self, *args, **kwargs)
		
		self.watchers = []
		
		if not is_meta(self.path):
			self.fs.on_eventcreated(self.path)

	def watch(self, watcher):
		if watcher not in self.watchers:
			self.watchers.append(watcher)
			watcher.send_eventcreated(self.path)

	def ignore(self, watcher):
		self.watchers.remove(watcher)

	def _raise(self, *args):
		if not is_meta(self.path):
			self.fs.on_raise(self.path, *args)
		
		for watcher in self.watchers:
			watcher.send_event(self.path, *args)

	def delete(self):
		if not is_meta(self.path):
			self.fs.on_eventdeleted(self.path)
		
		Node.delete(self)

		for watcher in self.watchers:
			watcher.send_eventdeleted(self.path)


class Action(Node):
	type = "action"

	def call(self, *args):
		if not is_meta(self.path):
			self.fs.on_call(self.path, *args)
		
		return self.owner.send_docall(self.path, *args)

