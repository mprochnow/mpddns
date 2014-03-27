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
        parsed_url = urlparse.urlparse(self.path)
        parsed_query = urlparse.parse_qs(parsed_url.query)
        
        if ("domain" not in parsed_query) or ("password" not in parsed_query) or ("ip" not in parsed_query):
            self.send_response(400)
        else:
            password = self.server.catalog.get_password(parsed_query["domain"][0])
            if password is not None:
                if password != parsed_query["password"][0]:
                    self.send_response(403)
                else:
                    self.server.catalog.update_ip(parsed_query["domain"][0], parsed_query["ip"][0])
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
