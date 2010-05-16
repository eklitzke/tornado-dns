import tornado.ioloop
import tornado_dns
        
def main():
    io_loop = tornado.ioloop.IOLoop.instance()

    def success(addresses):
        print 'addresses: %s' % (addresses,)
        io_loop.stop()

    def errback(code):
        print tornado_dns.errors.describe(code)
        io_loop.stop()

    tornado_dns.lookup("www.eklitzke.org", success, errback, timeout=5000)
    io_loop.start()

if __name__ == '__main__':
    main()
