from twisted.trial import unittest
from shet.server.file_system import FileSystem
from mock import Mock


class SimpleTests(unittest.TestCase):
	
	def setUp(self):
		self.fs = FileSystem()
	
	def test_add(self):
		m = Mock()
		self.fs.add("/foo/bar", m)
		self.assertEqual(self.fs.get_node("/foo/bar"), m)
	
	def test_remove(self):
		self.fs.add("/foo/bar", "baz")
		self.fs.remove("/foo/bar")
		
		self.assertRaises(Exception, lambda: self.fs.get_node("/foo/bar"))
		self.assertEqual(self.fs.list_dir(), {})
	
	def test_list_dir(self):
		m = Mock()
		self.fs.add("/foo/bar", m)
		
		self.assertEqual(self.fs.list_dir(),
		                 {'foo': {'bar': m.type}})
		
		self.assertEqual(self.fs.list_dir("/"),
		                 {'foo': {'bar': m.type}})
		
		self.assertEqual(self.fs.list_dir("/", False),
		                 {'foo': 'dir'})
		
		self.assertEqual(self.fs.list_dir("/foo", False),
		                 {'bar': m.type})


class EdgeCaseTests(unittest.TestCase):
	
	def setUp(self):
		self.fs = FileSystem()
	
	def test_add_same(self):
		self.fs.add("/foo/bar", "baz")
		self.assertRaises(Exception, lambda: self.fs.add("/foo/bar", "foo"))
	
	def test_add_over_dir(self):
		self.fs.add("/foo/bar", "baz")
		self.assertRaises(Exception, lambda: self.fs.add("/foo", "foo"))
	
	def test_remove_nonexistant(self):
		self.assertRaises(Exception, lambda: self.fs.remove("/foo"))
		self.assertRaises(Exception, lambda: self.fs.remove("/foo/bar"))
	
	def test_add_deeper(self):
		m = Mock()
		self.fs.add("/foo/bar", m)
		self.assertRaises(Exception, lambda: self.fs.add("/foo/bar/baz", "quux"))
