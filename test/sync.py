from twisted.internet import defer
from twisted.trial import unittest
from twisted.python.failure import Failure
from shet.sync import make_sync

class MakeSyncTests(unittest.TestCase):
    
    def test_no_yield(self):
        @make_sync
        def f():
            return 5
        return f().addCallback(self.assertEqual, 5)
    
    def test_return_deferred(self):
        a_d = defer.Deferred()
        @make_sync
        def f():
            return a_d
        d = f().addCallback(self.assertEqual, 2)
        a_d.callback(2)
        return d

    def test_yield_no_defer(self):
        @make_sync
        def f():
            self.assertEqual((yield 3), 3)
            yield 5
        return f().addCallback(self.assertEqual, 5)
    
    def test_defer(self):
        d = defer.Deferred()
        @make_sync
        def f():
            x = (yield d)
            yield x + 1
        d2 = f().addCallback(self.assertEqual, 6)
        d.callback(5)
        return d2
    
    def test_defer_twice(self):
        a_d = defer.Deferred()
        b_d = defer.Deferred()
        @make_sync
        def f():
            a = (yield a_d)
            b = (yield b_d)
            yield a + b
        d = f().addCallback(self.assertEqual, 5)
        a_d.callback(2)
        b_d.callback(3)
        return d
    
    def test_errback(self):
        a_d = defer.Deferred()
        b_d = defer.Deferred()
        @make_sync
        def f():
            a = (yield a_d)
            try:
                b = (yield b_d)
            except Exception, e:
                yield a + 1
        d = f().addCallback(self.assertEqual, 3)
        a_d.callback(2)
        b_d.errback(Exception("test"))
        return d
    
    def failureEqual(self, a, b):
        self.assertEqual(a.type, b.type)
        self.assertEqual(a.value.args, b.value.args)
        self.assertEqual(a.value.message, b.value.message)
    
    def test_exception(self):
        @make_sync
        def f():
            raise Exception("test")
        return f().addErrback(self.failureEqual, Failure(Exception("test")))
    
    def test_exception_and_yield(self):
        @make_sync
        def f():
            yield 5
            raise Exception("test")
        return f().addErrback(self.failureEqual, Failure(Exception("test")))
