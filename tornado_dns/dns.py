import socket

from tornado_dns._struct import *

class ParseError(Exception):
    pass

class DNSPacket(object):

    def __init__(self, raw=None):
        self.raw = raw

    @classmethod
    def create_with_header(cls, **kwargs):
        packet = cls()

        packet._questions = kwargs.get('questions', [])
        packet._answers = kwargs.get('answers', [])
        packet._authorities = kwargs.get('authorities', [])
        packet._additionals = kwargs.get('additionals', [])

        packet.id = read_counter()
        packet.qr = 0
        packet.opcode = 0
        packet.aa = 0
        packet.tc = 0
        packet.rd = 1
        packet.ra = 0
        packet.rcode = 0
        packet.qdcount = len(packet._questions)
        packet.ancount = len(packet._answers)
        packet.nscount = len(packet._authorities)
        packet.arcount = len(packet._additionals)

        overrides = dict((k, v) for k, v in kwargs.iteritems() if not k not in ('questions', 'answers', 'authorities', 'additionals'))
        packet.__dict__.update(overrides)
        return packet

    @classmethod
    def create_a_question(cls, name):
        return cls.create_with_header(questions=[AQuestion(name)])

    @classmethod
    def create_ptr_question(cls, address):
        return cls.create_with_header(questions=[PTRQuestion(address)])

    @classmethod
    def from_wire(cls, data):
        packet = cls(data)

        reader = StructReader(data)
        packet.id = reader.read_num(16)
        packet.qr = reader.read_bits(1)
        packet.opcode = reader.read_bits(4)
        packet.aa = reader.read_bits(1)
        packet.tc = reader.read_bits(1)
        packet.rd = reader.read_bits(1)
        packet.ra = reader.read_bits(1)
        if reader.read_bits(3) != 0:
            raise ParseError('Z section was non-zero')
        packet.rcode = reader.read_bits(4)
        if packet.rcode != 0:
            raise ParseError('rcode = %d' % (rcode,))
        packet.qdcount = reader.read_num(16)
        packet.ancount = reader.read_num(16)
        packet.nscount = reader.read_num(16)
        packet.arcount = reader.read_num(16)

        packet._questions = [Question.from_wire(reader) for x in xrange(packet.qdcount)]
        packet._answers = [ResourceRecord.from_wire(reader) for x in xrange(packet.ancount)]
        packet._authorities = [None for x in xrange(packet.nscount)]
        packet._additionals = [None for x in xrange(packet.arcount)]
        return packet

    def to_wire(self):
        builder = StructBuilder()
        builder.push_num(self.id, 16)
        builder.push_bits(self.qr, 1)
        builder.push_bits(self.opcode, 4)
        builder.push_bits(self.aa, 1)
        builder.push_bits(self.tc, 1)
        builder.push_bits(self.rd, 1)
        builder.push_bits(self.ra, 1)
        builder.push_bits(0, 3) # reserved bits
        builder.push_bits(self.rcode, 4)
        builder.push_num(self.qdcount, 16)
        builder.push_num(self.ancount, 16)
        builder.push_num(self.nscount, 16)
        builder.push_num(self.arcount, 16)

        def add_section(sections):
            for s in sections:
                s.build(builder)

        add_section(self._questions)
        add_section(self._answers)
        add_section(self._authorities)
        add_section(self._authorities)
        return builder.read()

    def get_answer_names(self):
        cnames = set()
        results = {}
        for ans in self._answers:
            tn = ans.type_name()
            if tn in ('A', 'MX'):
                results[ans.name] = ans._value
            elif tn == 'CNAME':
                cnames.add(ans)

        # Try to resolve all of the CNAMES. This is a naive algorithm that could
        # take O(N) steps in the worst case (i.e. if the CNAMEs are listed in
        # the reverse linearized order)
        while True:
            reduced = set()
            for cname in cnames:
                if cname._value in results:
                    results[cname.name] = results[cname._value]
                    reduced.add(cname)
            if not reduced:
                for cname in cnames:
                    results[cname.name] = None # we were unable to resolve this CNAME
                break
            else:
                cnames = cnames - reduced
                if not cnames:
                    break
        return results

class Question(object):

    qtype = 0

    def __init__(self, name):
        self.qname = name
        self.qclass = 1 # IN

    def build(self, builder):
        name = self.qname
        if name[-1] != '.':
            name += '.'
        while name:
            pos = name.find('.')
            builder.push_string(chr(pos) + name[:pos])
            name = name[pos + 1:]
        builder.push_string(chr(0))
        builder.push_num(self.qtype, 16) # TYPE = self.rdtype
        builder.push_num(1, 16) # QCLASS = IN

    @classmethod
    def from_wire(cls, reader):
        name = reader.read_name()
        qtype = reader.read_num(16)
        qclass = reader.read_num(16)
        q = Question(name)
        q.qtype = qtype
        q.qclass = qclass
        return q

    def __str__(self):
        return '%s(qname=%r, qtype=%d, qclass=%d)' % (self.__class__.__name__, self.qname, self.qtype, self.qclass)
    __repr__ = __str__

class AQuestion(Question):
    qtype = 1

class PTRQuestion(Question):
    qtype = 12

    def __init__(self, address):
        self.address = address
        name = '.'.join(reversed(address.split('.'))) + '.in-addr.arpa'
        super(PTRQuestion, self).__init__(name)

class ResourceRecord(object):
    
    def __init__(self):
        self._value = None

    @classmethod
    def from_wire(cls, reader):
        rr = cls()
        rr.name = reader.read_name()
        rr.type = reader.read_num(16)
        rr.class_ = reader.read_num(16)
        rr.ttl = reader.read_num(32)
        rr.rdlength = reader.read_num(16)
        rr.rdata = reader.read_bytes(rr.rdlength)

        if rr.type_name() in ('A', 'MX'):
            rr._value = socket.inet_ntoa(rr.rdata)
        elif rr.type_name() == 'CNAME':
            with reader.mock_position(reader.pos - rr.rdlength):
                rr._value = reader.read_name()
        return rr

    def type_name(self):
        types = {
            1: 'A',
            2: 'NS',
            3: 'MD',
            4: 'MF',
            5: 'CNAME',
            6: 'SOA',
            7: 'MB',
            8: 'MG',
            9: 'MR',
            10: 'NULL',
            11: 'WKS',
            12: 'PTR',
            13: 'HINFO',
            14: 'MINFO',
            15: 'MX',
            16: 'TXT'
        }
        return types.get(self.type, '<%d>' % self.type)

    def class_name(self):
        return 'IN' if self.class_ == 1 else '<%d>' % self.class_

    def is_address(self):
        return self.class_ == 1 and self.type_name() in ('A', 'MX')

    def read_address(self):
        return socket.inet_ntoa(self.rdata)

    def __str__(self):
        return '%s(name=%r, type=%s, class=%s, ttl=%d, rdlength=%d)' % (self.__class__.__name__, self.name, self.type_name(), self.class_name(), self.ttl, self.rdlength)
    __repr__ = __str__
