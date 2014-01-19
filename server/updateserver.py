import binascii
import hashlib
import hmac
import os
import select
import socket
import SocketServer
from syslog import syslog
import threading
import traceback

class UpdateRequestHandler(SocketServer.BaseRequestHandler):
    timeout = 1 # just an estimate

    def setup(self):
        if self.timeout:
            self.request.settimeout(self.timeout)

    def handle(self):
        challenge = binascii.b2a_hex(os.urandom(15))

        self.request.sendall(challenge + "\r\n")

        try:
            response = self.request.recv(1024)
        except socket.timeout:
            pass
        else:
            pos = response.find(" ")
            if pos:
                domain = response[:pos]

                digest = response[pos + 1:]
                pos = digest.find("\r\n")
                if pos:
                    digest = digest[:pos]

                    if len(digest):
                        password = str(self.server.catalog.getPassword(domain))

                        if hmac.new(password, challenge, hashlib.sha256).hexdigest() == digest:
                            self.server.catalog.updateIp(domain, self.client_address[0])

class UpdateServer(threading.Thread):
    def __init__(self, address, catalog):
        threading.Thread.__init__(self)

        SocketServer.TCPServer.allow_reuse_address = True
        self.server = SocketServer.TCPServer(address, UpdateRequestHandler)
        self.server.timeout = 0.1
        self.server.catalog = catalog

        self.cancel = False

    def run(self):
        while not self.cancel:
            try:
                self.server.handle_request()
            except select.error:
                pass # ignoring it, happens when select call will be interrupted by user change
            except:
                syslog(traceback.format_exc())

    def stop(self):
        self.cancel = True
