Basics
======

This lets you do asynchronous DNS lookups using Tornado. Look at `example.py`
for an example of a very simple program that does a DNS lookup.

Only a basic subset of operations is supported. Right now, the following things work:

 * Resolving A records
 * Resolving CNAME records

This is approximately the functionality implemented by `gethostbyname(3)`. There
are plans to implement support for at least the following, in short order:

 * Resolving PTR records (a.k.a. "reverse DNS")
 * Resolving MX records
 * Resolving TXT records

There are no immediate plans for implementing other, exotic features of DNS. DNS
is surprisingly complex, and the author feels that too many implementors of DNS
libraries go overboard creating comprehensive, but complex and hard-to-use
software. This library keeps it simple; if you want something that implements
the absolutely everything, including all of the exotic, rarely used parts of the
DNS specs, you may consider using [dns-python](http://www.dnspython.org/) with
your own resolver.

Basic Usage:
------------

The most basic possible usage:

    def success(addresses):
        print 'addresses: %s' % (addresses,)
    
    # timeout after 5000 milliseconds
    tornado_dns.lookup("www.eklitzke.org", success, timeout=5000)

You'll need to do the lookup in the context of a tornado IOLoop that's
running. Look at `example.py` for a very slightly more example.

More Nonsense
=============

Dependencies
------------

This software depends on tornado, and that's it. There's one more non-standard
module you'll need if you're interested in running the unit tests (see below),
but other than that everything you need is right here.

Bugs
----

There's no support for fallback to TCP. This is something I'd like to fix.

There's no support for non-recursive queries. In particular, you must have a
nameserver in your `/etc/resolv.conf` that's capable of performing recursive DNS
lookups. This should be OK for 99.9% of people, but it's something I'd like to
fix anyway.

Tests
-----

This code comes with unit tests that test against a domain that the author
owns/controls. They should pass. To run them, you'll need the
[qa](http://github.com/bickfordb/qa) module in your `PYTHONPATH`. Just run
`./runtests` and you should see some text showing that everything is OK.

Licensing
---------

This code is licensed under the terms of the
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html). This
is the same license used by the main Tornado project.
