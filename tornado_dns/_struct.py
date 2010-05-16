from __future__ import with_statement

from contextlib import contextmanager
import threading
import struct

_counter = threading.local()

def read_counter():
    value = getattr(_counter, 'value', 1)
    _counter.value = value + 1
    return value

def ntoh16(s):
    return (ord(s[0]) << 8) + ord(s[1])

def ntoh32(s):
    hi = ntoh16(s)
    lo = ntoh16(s[2:])
    return (hi << 16) + lo

class StructError(Exception):
    pass

class StructBuilder(object):

    def __init__(self):
        self.clear()

    def _add_byte(self, val=None):
        self.bytes.append(struct.pack("B", val))

    def push_bits(self, val, bits):
        assert bits <= 8
        self.trailing_bits += bits
        self.trailing_val <<= bits
        self.trailing_val += val

        if self.trailing_bits == 8:
            self._add_byte(self.trailing_val)
            self.trailing_val = 0
            self.trailing_bits = 0

    def push_num(self, val, bits):
        """Push a number onto the structure. This method will ensure that the
        message is encoded in big-endian order.
        """
        assert bits % 8 == 0
        nums = []
        while bits:
            nums.append(val % 256)
            val >>= 8
            bits -= 8
        for n in reversed(nums):
            self._add_byte(n)

    def push_string(self, val):
        self.bytes.append(val)

    def read(self):
        if self.trailing_bits != 0:
            raise ValueError("Non-byte aligned bits")
        return ''.join(self.bytes)

    def clear(self):
        self.bytes = []
        self.trailing_bits = 0
        self.trailing_val = 0

class StructReader(object):

    def __init__(self, bytes, pos=0):
        self.bytes = bytes
        self.pos = pos
        self.trailing_val = 0
        self.trailing_bits = 0

    @contextmanager
    def mock_position(self, new_pos):
        old_pos = self.pos
        self.pos = new_pos
        yield
        self.pos = old_pos

    def read_bits(self, bits):
        if self.trailing_bits == 0:
            self.trailing_val = self.read_num(8)
            self.trailing_bits = 8
        val = self.trailing_val >> (self.trailing_bits - bits)
        self.trailing_bits -= bits
        self.trailing_val &= ((1 << self.trailing_bits) - 1)
        if self.trailing_bits < 0:
            raise ValueError
        return val

    def read_num(self, bits):
        if self.pos > len(self.bytes):
            raise StructError("self.pos = %d, len(self.bytes) = %d" % (self.pos, len(self.bytes)))
        if bits == 8:
            val = ord(self.bytes[self.pos])
            self.pos += 1
        elif bits == 16:
            val = ntoh16(self.bytes[self.pos:])
            self.pos += 2
        elif bits == 32:
            val = ntoh32(self.bytes[self.pos:])
            self.pos += 4
        else:
            raise NotImplementedError
        return val

    def read_name(self, strip_trailing_dot=True):
        if self.pos > len(self.bytes):
            raise StructError("self.pos = %d, len(self.bytes) = %d" % (self.pos, len(self.bytes)))

        name = ''
        while True:
            count = self.read_num(8)
            if count == 0:
                break
            if count <= 63:
                name += self.read_bytes(count) + '.'
            elif count >= 192:
                # read an offset label, RFC 1035 section 4.1.4
                next_pos = self.pos + 1
                self.pos -= 1
                self.pos = self.read_num(16) & 0x3fff
                name += self.read_name(strip_trailing_dot=False)
                self.pos = next_pos # XXX: what did I flub here?
                break

        if strip_trailing_dot:
            name = name[:-1]
        return name

    def read_bytes(self, length):
        if self.pos > len(self.bytes):
            raise StructError("self.pos = %d, len(self.bytes) = %d" % (self.pos, len(self.bytes)))
        data = self.bytes[self.pos:self.pos+length]
        self.pos += length
        return data

__all__ = ['read_counter', 'StructBuilder', 'StructReader']
