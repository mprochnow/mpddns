#!/usr/bin/env python

# This file is part of mpddns.
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mpddns.  If not, see <http://www.gnu.org/licenses/>.

import hashlib
import hmac
import optparse
import socket
import syslog

if __name__ == '__main__':
    syslog.openlog("mpddns_client")

    parser = optparse.OptionParser()
    parser.add_option("-s", "--server", help="Host of mpddns server")
    parser.add_option("-p", "--port", help="Port of mpddns server (default: 7331)")
    parser.add_option("-H", "--host", help="Hostname to update")
    parser.add_option("-P", "--password", help="Password to authenticate")
    options, args = parser.parse_args()

    server = options.server
    port = options.port
    host = options.host
    password = options.password

    if server is None or host is None or password is None or (port and not port.isdigit()):
        parser.print_help()
        parser.exit()

    portnum = 7331
    if port:
        portnum = int(port)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, portnum))
    d = s.recv(1024)

    digest = hmac.new(password, d[:-2], hashlib.sha256).hexdigest()

    s.sendall(host + " " + digest + "\r\n")
    s.close()

    syslog.syslog("Updated mpddns server")
