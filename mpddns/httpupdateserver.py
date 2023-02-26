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

import http.server
import logging
import urllib.parse
import threading
import select

logger = logging.getLogger("mpddns")


class HTTPUpdateRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "mpddns"
    timeout = 1  # just an estimate

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        parsed_query = urllib.parse.parse_qs(parsed_url.query)

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

        self.server = http.server.HTTPServer(address, HTTPUpdateRequestHandler)
        self.server.socket.settimeout(self.timeout)
        self.server.catalog = catalog

        self.cancel = False

    def run(self):
        while not self.cancel:
            try:
                self.server.handle_request()
            except select.error:
                pass  # ignoring it, happens when select call will be interrupted by user change
            except Exception as e:
                logger.error(f"Unhandled exception in HTTP update server loop: {e}")

    def stop(self):
        self.cancel = True
