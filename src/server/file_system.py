import os.path
from collections import defaultdict

def is_meta(path):
	return path.startswith("/meta/")

class DirectoryTree(dict):
	
	type = "dir"
	
	def __init__(self, parent=None):
		dict.__init__(self)
		self.parent = parent
	
	def add_get(self, key):
		try:
			return self[key]
		except KeyError:
			new_dir = DirectoryTree(self)
			self[key] = new_dir
			return new_dir
	
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


	def get_node(self, path, add=False):
		parts = self.split_path(path)
		if not parts:
			return self.root
		parent = self.get_node(self.join_path(parts[:-1]), add)
		return parent.add_get(parts[-1]) if add else parent[parts[-1]]

	
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
					for sub_path in self.list_full_paths(os.path.join(path,
					                                                  name)):
						yield os.path.join(name,
						                   sub_path)
				else:
					yield name
				
			
	def add(self, full_path, node):
		path, name = os.path.split(full_path)
		
		assert name, Exception("Must specify a file.")

		self.get_node(path, True)[name] = node
		self.on_change("add", full_path)


	def remove(self, path):
		parts = self.split_path(path)
		
		del self.get_node(self.join_path(parts[:-1]))[parts[-1]]
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
		return self.owner.send_get(self.path)

	def set(self, value):
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
		return self.owner.send_docall(self.path, *args)

