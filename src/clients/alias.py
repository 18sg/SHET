from shet.client import ShetClient
from shet.sync import make_sync

from pickle import dump, load


class Alias(ShetClient):
	
	def __init__(self):
		self.root = "/util/alias"
		self.db = "alias.db"
		ShetClient.__init__(self)
		
		self.add_action("create", self.create_alias)
		
		self.add_action("ls", self.ls)
		self.add_action("rm", self.rm)
		
		self.watch_event("/meta/on_tree_change", self.on_tree_change)
		
		self.aliases = []
		self.alias_shet = {}
		self.load_aliases()
	
	
	def on_tree_change(self, type, target):
		try:
			alias = filter((lambda a: a[0] == target), self.aliases)[0][1]
		except IndexError:
			# Not an alias
			return
		
		if type == "add":
			try:
				self.add_alias(alias)
			except IndexError:
				# Not one of the aliases
				pass
			
		elif type == "remove":
			try:
				self.remove_alias(alias)
			except IndexError:
				# Not one of the aliases
				pass
	
	
	def store_aliases(self):
		b = self.aliases[:]
		dump(b, open(self.db, "w"))
	
	
	def load_aliases(self):
		try:
			for target, alias in load(open(self.db, "r")):
				self.create_alias(target, alias)
		except IOError:
			pass
	
	
	def create_alias(self, target, alias):
		self.aliases.append((target, alias))
		self.store_aliases()
		try:
			self.add_alias(alias)
		except Exception, e:
			self.aliases.remove((target, alias))
			self.store_aliases()
			raise(e)
	
	
	def ls(self):
		return self.aliases
	
	
	def rm(self, alias):
		try:
			self.remove_alias(alias)
		finally:
			to_delete = filter((lambda a: a[1] == alias), self.aliases)
			map(self.aliases.remove, to_delete)
			self.store_aliases()
	
	
	@make_sync
	def add_alias(self, alias):
		target = filter((lambda a: a[1] == alias), self.aliases)[0][0]
		
		type = (yield self.call("/meta/type", target))
		
		if type == "action":
			self.alias_shet[alias] = self.add_action(alias, (lambda *a: self.call(target, *a)))
			self.alias_shet[alias].type = "action"
		elif type == "event":
			print "evt"
			self.alias_shet[alias] = self.add_event(alias)
			self.alias_shet[alias].watcher = self.watch_event(target, self.alias_shet[alias])
			self.alias_shet[alias].type = "event"
		elif type == "prop":
			self.alias_shet[alias] = self.add_property(alias,
			                            (lambda *a: self.get(target, *a)),
			                            (lambda *a: self.set(target, *a)))
			self.alias_shet[alias].type = "prop"
	
	def remove_alias(self, alias):
		type = self.alias_shet[alias].type
		
		if type == "action":
			self.remove_action(self.alias_shet[alias])
		elif type == "event":
			self.unwatch_event(self.alias_shet[alias].watcher)
			self.remove_event(self.alias_shet[alias])
		elif type == "prop":
			self.remove_property(self.alias_shet[alias])
		
		del self.alias_shet[alias]


if __name__ == "__main__":
	Alias().run()
