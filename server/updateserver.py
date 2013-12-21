import binascii
import hashlib
import hmac
import os
import SocketServer
from syslog import syslog
import threading
import traceback

class UpdateRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        challenge = binascii.b2a_hex(os.urandom(15))

        self.request.sendall(challenge + "\r\n")

        response = self.request.recv(1024)
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
            except:
                syslog(traceback.format_exc())

    def stop(self):
        self.cancel = True

if __name__ == "__main__":
    import socket

    srv = UpdateServer(("0.0.0.0", 1337), None)
    srv.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("0.0.0.0", 1337))
    d = s.recv(1024)

    digest = hmac.new("password123", d[:-2], hashlib.sha256).hexdigest()

    print digest

    s.sendall("home.martin-prochnow.de " + digest + "\r\n")
    s.close()

    srv.stop()
