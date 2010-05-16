# Naive parser for resolv.conf. See resolv.conf(5)

import re
import socket

_nameservers = None

def get_nameservers():
    global _nameservers
    if _nameservers is None:
        _nameservers = []
        regex = re.compile(r'^nameserver ([\d\.]+)\s*$')
        try:
            for line in open('/etc/resolv.conf'):
                match = regex.match(line)
                if match:
                    _nameservers.append(match.groups()[0])
        except IOError:
            pass
    return _nameservers

__all__ = ['get_nameservers']
