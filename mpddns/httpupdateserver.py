import BaseHTTPServer
import logging
import urlparse
import threading

class HTTPUpdateRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "mpddns"
    timeout = 1 # just an estimate

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsedURL = urlparse.urlparse(self.path)
        parsedQuery = urlparse.parse_qs(parsedURL.query)
        
        if ("domain" not in parsedQuery) or ("password" not in parsedQuery) or ("ip" not in parsedQuery):
            self.send_response(400)
        else:
            password = self.server.catalog.getPassword(parsedQuery["domain"][0])
            if password is not None:
                if password != parsedQuery["password"][0]:
                    self.send_response(403)
                else:
                    self.server.catalog.updateIp(parsedQuery["domain"][0], parsedQuery["ip"][0])
                    self.send_response(200)
            else:
                self.send_response(404)

            self.end_headers()

class HTTPUpdateServer(threading.Thread):
    timeout = 0.1

    def __init__(self, address, catalog):
        threading.Thread.__init__(self)

        self.server = BaseHTTPServer.HTTPServer(address, HTTPUpdateRequestHandler)
        self.server.socket.settimeout(self.timeout)
        self.server.catalog = catalog

        self.cancel = False

    def run(self):
        while not self.cancel:
            try:
                self.server.handle_request()
            except select.error:
                pass # ignoring it, happens when select call will be interrupted by user change
            except:
                logging.exception("Unhandled exception in HTTP update server loop")

    def stop(self):
        self.cancel = True
