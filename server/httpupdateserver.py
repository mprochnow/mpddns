import BaseHTTPServer
import urlparse
import syslog
import threading
import traceback

class HTTPUpdateRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsedURL = urlparse.urlparse(self.path)
        parsedQuery = urlparse.parse_qs(parsedURL.query)
        
        if ("domain" not in parsedQuery) or ("password" not in parsedQuery) or ("ip" not in parsedQuery):
            self.send_response(400)
            self.end_headers()
            return
	
        password = str(self.server.catalog.getPassword(parsedQuery["domain"][0]))

        if parsedQuery["password"][0] != password:
            self.send_response(401)
            self.end_headers()
            return

        status = self.server.catalog.updateIp(parsedQuery["domain"][0], parsedQuery["ip"][0])
	    
        if status:
            self.send_response(200)
            self.end_headers()
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
            except:
                syslog.syslog(syslog.LOG_CRIT, traceback.format_exc())

    def stop(self):
        self.cancel = True
