import qa
from contextlib import contextmanager
from functools import wraps
import tornado.ioloop
import tornado_dns

io_loop = tornado.ioloop.IOLoop.instance()

class Trit(object):

    OFF = 0
    ON = 1
    ERR = 2

    def __init__(self):
        self.val = self.OFF
        self.val = False

    def on(self):
        self.val = True

    def off(self):
        self.val = False

    def check(self, expected=None):
        if expected is None:
            expected = self.ON
        if self.val != expected:
            raise AssertionError("Expected %s, got %s" % (self.read_val(expected), self.read_val()))

    def read_val(self, val=None):
        if val is None:
            val = self.val
        if val == self.OFF:
            return 'OFF'
        elif val == self.ON:
            return 'ON'
        elif val == self.ERR:
            return 'ERR'
        else:
            raise ValueError('val = %r' % (val,))

@contextmanager
def test_context(ctx):
    ctx.trit_final = Trit.ON
    ctx.trit = Trit()
    yield
    ctx.trit.check(ctx.trit_final)

def callback(func):
    @wraps(func)
    def inner(*args, **kwargs):
        ret = func(*args, **kwargs)
        io_loop.stop()
        return ret
    return inner

def testcase(*extra_requires):
    def outer(func):
        @qa.testcase(requires=[test_context] + list(extra_requires))
        @wraps(func)
        def inner(ctx):
            def run():
                return func(ctx)
            io_loop.add_callback(run)
            io_loop.start()
        return inner
    return outer

@testcase()
def test_basic_a_record(ctx):
    @callback
    def success(records):
        ctx.trit.on()
        assert records['iomonad.com'] == '173.230.147.249'
    tornado_dns.lookup('iomonad.com', success)

@testcase()
def test_simple_cname(ctx):
    @callback
    def success(records):
        ctx.trit.on()
        assert records['cname1.iomonad.com'] == '173.230.147.249'
        assert records['cname1.iomonad.com'] == records['iomonad.com']
    tornado_dns.lookup('cname1.iomonad.com', success)

@testcase()
def test_complex_cname(ctx):
    @callback
    def success(records):
        ctx.trit.on()
        assert records['cname2.iomonad.com'] == '173.230.147.249'
        assert records['cname2.iomonad.com'] == records['cname1.iomonad.com']
        assert records['cname1.iomonad.com'] == records['iomonad.com']
    tornado_dns.lookup('cname2.iomonad.com', success)

if __name__ == '__main__':
    qa.main()
