from twisted.internet import defer
from functools import wraps

__all__ = ["make_sync"]

def make_sync(f):
    """A decorator to turn a generator into a deferred function.
    
    To wait for a deferred value to resolve, the decorated function should
    yield it; the result will be passed back when it's callbacks run, or an
    exception will be raised when it's errbacks run. The last value to be
    yielded will be the return value of the function. If an exception is raised
    the errback will be triggered.
    
    Example:
        @make_sync
        def new_function_that_returns_deferred():
            x = (yield deferred_int_returning_function())
            yield x + 1
    """
    @wraps(f)
    def g(*args, **kwargs):
        finished = defer.Deferred()
        
        try:
            gen = f(*args, **kwargs)
        except Exception, e:
            finished.errback(e)
            return finished
        
        # If the decorator was used when it wasn't needed, it may well return a
        # deferred, which should not be passed through another deferred.
        if isinstance(gen, defer.Deferred):
            return gen
        
        # If the function did not return a generator, return straight away.
        if not (hasattr(gen, "next") and hasattr(gen, "send")):
            finished.callback(gen)
            return finished
        
        # Step forward in the generator code, using the supplied function and
        # arguments, f(*args). This should return a Deferred (yielded by the
        # generator); callbacks are added such that when this generator completes,
        # the value is passed back to the generator, using either gen.send or
        # gen.throw. If StopIteration is raised because the generator has finished,
        # complete finished with the supplied x value; the last generated value. If
        # another exception is raised by the generator, pass it to finished.
        def step(x, f, *args):
            try:
                d = f(*args)
                if isinstance(d, defer.Deferred):
                    d.addCallbacks(callback, errback)
                else:
                    callback(d)
            except StopIteration:
                finished.callback(x)
            except Exception, e:
                finished.errback(e)
        
        def callback(x):
            step(x, gen.send, x)
        
        def errback(e):
            step(None, gen.throw, e.type, e.value)
        
        step(None, gen.next)
        
        return finished

    return g

