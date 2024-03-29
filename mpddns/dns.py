# This file is part of mpddns.
#
# mpddns is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mpddns is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mpddns.  If not, see <http://www.gnu.org/licenses/>.

import ipaddress
import struct


class Opcode:
    STANDARD = 0
    INVERSE = 1
    SERVER_STATUS = 2


class Type:
    A = 1
    NS = 2
    CNAME = 5
    SOA = 6
    WKS = 11
    PTR = 12
    HINFO = 14
    MX = 15
    TXT = 16


class Class:
    IN = 1
    CH = 3
    HS = 5
    ANY = 255


class Rcode:
    NO_ERROR = 0
    FORMAT_ERROR = 1  # Unable to interpret query
    SERVER_FAILURE = 2  # Unable to process query because of internal problems
    NAME_ERROR = 3  # Queried domain name does not exists
    NOT_IMPLEMENTED = 4  # Requested query not supported
    REFUSED = 5  # Server refuses to process query


class Header:
    Size = 12
    Format = struct.Struct(">6H")

    def __init__(self, data):
        raw = Header.Format.unpack_from(data)

        self.id = raw[0]
        self.qr = (raw[1] & 0x8000) >> 15
        self.opcode = (raw[1] & 0x7800) >> 11
        self.qdCount = raw[2]
        self.anCount = raw[3]
        self.nsCount = raw[4]
        self.arCount = raw[5]


class Question:
    Format = struct.Struct(">2H")

    def __init__(self, data, offset):
        qname = ''
        while True:
            length, = struct.unpack_from(">B", data, offset)
            offset += 1

            if length == 0:
                self.qname = qname
                self.offset = offset
                break

            label = struct.unpack_from(">%ds" % length, data, offset)
            qname += label[0].decode("ascii") + "."

            offset += length

        qtype, qclass = Question.Format.unpack_from(data, offset)
        self.offset += Question.Format.size

        self.qtype = qtype
        self.qclass = qclass

    def get(self):
        result = ''.join([chr(len(x)) + x for x in self.qname.split('.')]).encode('ascii')
        result += DnsQuery.QuerySectionFormat.pack(self.qtype, self.qclass)

        return result


class DnsQuery:
    QuerySectionFormat = struct.Struct(">2H")

    def __init__(self, data):
        self.valid = False
        self.header = None
        self.questions = []

        if len(data) >= Header.Format.size:
            self.header = Header(data)

            if self.header.qdCount and len(data) > Header.Size:
                # parse questions
                offset = Header.Format.size
                for _ in range(self.header.qdCount):
                    question = Question(data, offset)
                    offset = question.offset

                    self.questions.append(question)

                self.valid = True

    def response(self, rcode, question=None, ip=None):
        result = Header.Format.pack(self.header.id,  # id
                                    0x8400 | (rcode & 0x0f),  # header
                                    0x0001 if question else 0x0000,  # qdcount
                                    0x0001 if rcode == Rcode.NO_ERROR else 0x0000,  # ancount
                                    0x0000,  # nscount
                                    0x0000)  # arcount

        if question:
            result += question.get()

        if rcode == Rcode.NO_ERROR:
            result += struct.pack(
                ">HHHLHL",
                0xc000 | 0x000c,  # pointer to domain name
                Type.A,
                Class.IN,
                0x00000000,  # ttl
                0x0004,  # rdlength
                int(ipaddress.IPv4Address(ip))  # A record
            )

        return result
