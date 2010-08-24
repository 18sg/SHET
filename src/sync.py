from twisted.internet import reactor
from twisted.internet import defer
from shet.error import ShetException

__all__ = ["make_sync"]

def make_sync(f):
    def g(*args, **kwargs):
        finished = defer.Deferred()
        gen = f(*args, **kwargs)

        if not (hasattr(gen, "next") and hasattr(gen, "send")):
            finished.callback(gen)

        def callback(x):
            try:
                d = gen.send(x)
                if isinstance(d, defer.Deferred):
                    d.addCallback(callback)
                    d.addErrback(errback)
                else:
                    callback(d)
            except StopIteration:
                finished.callback(x)
            except Exception, e:
                finished.errback(e)
        
        def errback(e):
            print e.value
            gen.throw(ShetException(e.value))

        try:
            d = gen.next()
            if isinstance(d, defer.Deferred):
                d.addCallback(callback)
                d.addErrback(errback)
            else:
                callback(d)
        except StopIteration:
            finished.callback(d)
        except Exception, e:
            finished.errback(e)

        return finished

    return g
