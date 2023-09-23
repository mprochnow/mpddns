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
import hashlib
import hmac
import logging
import os
import select
import socket
import socketserver
import threading

log = logging.getLogger(__name__)


class UpdateRequestHandler(socketserver.BaseRequestHandler):
    timeout = 1  # just an estimate

    def setup(self):
        if self.timeout:
            self.request.settimeout(self.timeout)

    def handle(self):
        log.debug(f"{self.request.client_address[0]} - Client opened connection")

        challenge = binascii.b2a_hex(os.urandom(15))

        self.request.sendall(challenge + "\r\n".encode('ascii'))
        log.debug(f"{self.request.client_address[0]} - Challenge sent to client")

        try:
            response = self.request.recv(1024).decode('ascii')
        except socket.timeout:
            pass
        except ValueError:
            pass
        else:
            log.debug(f"{self.request.client_address[0]} - Response received from client - {response}")

            pos = response.find(" ")
            if pos:
                domain = response[:pos]

                digest = response[pos + 1:]
                pos = digest.find("\r\n")
                if pos:
                    digest = digest[:pos]

                    if len(digest):
                        password = str(self.server.catalog.get_password(domain))

                        if hmac.new(password.encode('ascii'), challenge, hashlib.sha256).hexdigest() == digest:
                            self.server.catalog.update_ip(domain, self.client_address[0])


class UpdateServer(threading.Thread):
    def __init__(self, address, catalog):
        threading.Thread.__init__(self)

        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer(address, UpdateRequestHandler)
        self.server.timeout = 0.1
        self.server.catalog = catalog

        self.cancel = False

    def run(self):
        while not self.cancel:
            try:
                self.server.handle_request()
            except select.error:
                pass  # ignoring it, happens when select call will be interrupted by user change
            except:
                log.exception("Unhandled exception in update server loop")

    def stop(self):
        self.cancel = True
