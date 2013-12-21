import SocketServer
from syslog import syslog
import traceback
import threading

import dns

class DnsRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        socket = self.request[1]

        dnsQuery = dns.DnsQuery(data)

        if not dnsQuery.valid:
            syslog("Received invalid request")
            dnsQueryResponse = dnsQuery.response(dns.Rcode.FormatError);
        elif not len(dnsQuery.questions):
            syslog("Received request without question")
            dnsQueryResponse = dnsQuery.response(dns.Rcode.Refused)
        else:
            question = dnsQuery.questions[0]

            ip = self.server.catalog.getIp(question.qname[:-1])

            if not ip:
                syslog("No IP for '%s' found" % (question.qname[:-1]))
                dnsQueryResponse = dnsQuery.response(dns.Rcode.NameError, question)
            else:
                syslog("Found IP '%s' for '%s'" % (ip, question.qname[:-1]))
                dnsQueryResponse = dnsQuery.response(dns.Rcode.NoError, question, ip)

        socket.sendto(dnsQueryResponse, self.client_address)

class DnsServer(threading.Thread):
    def __init__(self, address, catalog):
        threading.Thread.__init__(self)

        self.server = SocketServer.UDPServer(address, DnsRequestHandler)
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

