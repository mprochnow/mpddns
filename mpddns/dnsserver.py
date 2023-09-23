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
import binascii
import logging
import struct

import select
import socketserver
import threading

from mpddns import dns

log = logging.getLogger(__name__)


class DnsRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        socket = self.request[1]

        try:
            dns_query = dns.DnsQuery(data)

            if not dns_query.valid:
                log.error(f"{self.client_address[0]} - Received invalid request")
                dns_query_response = dns_query.response(dns.Rcode.FORMAT_ERROR)
            elif not len(dns_query.questions):
                log.error(f"{self.client_address[0]} - Received request without question")
                dns_query_response = dns_query.response(dns.Rcode.REFUSED)
            else:
                question = dns_query.questions[0]

                ip = self.server.catalog.get_ip(question.qname[:-1])

                if not ip:
                    log.info(f"{self.client_address[0]} - No IP for '{question.qname[:-1]}' found")
                    dns_query_response = dns_query.response(dns.Rcode.NAME_ERROR, question)
                else:
                    log.info(f"{self.client_address[0]} - Found IP '{ip}' for '{question.qname[:-1]}'")
                    dns_query_response = dns_query.response(dns.Rcode.NO_ERROR, question, ip)

            socket.sendto(dns_query_response, self.client_address)
        except struct.error as e:
            log.error(f"{self.client_address[0]} - Error while parsing DNS query message "
                      f"({binascii.b2a_hex(data)}): {e}")


class DnsServer(threading.Thread):
    def __init__(self, address, catalog):
        threading.Thread.__init__(self)

        self.server = socketserver.UDPServer(address, DnsRequestHandler)
        self.server.timeout = 0.1
        self.server.catalog = catalog

        self.cancel = False

    def run(self):
        while not self.cancel:
            try:
                self.server.handle_request()
            except select.error:
                pass  # ignoring it, happens when select call will be interrupted by user change
            except Exception as e:
                log.error(f"Unhandled exception in DNS server loop: e")

    def stop(self):
        self.cancel = True
