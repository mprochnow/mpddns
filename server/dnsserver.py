import logging
import select
import SocketServer
import threading

import dns

class DnsRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        socket = self.request[1]

        dnsQuery = dns.DnsQuery(data)

        if not dnsQuery.valid:
            logging.error("%s - Received invalid request" % (self.client_address[0]))
            dnsQueryResponse = dnsQuery.response(dns.Rcode.FormatError);
        elif not len(dnsQuery.questions):
            logging.error("%s - Received request without question" % (self.client_address[0]))
            dnsQueryResponse = dnsQuery.response(dns.Rcode.Refused)
        else:
            question = dnsQuery.questions[0]

            ip = self.server.catalog.getIp(question.qname[:-1])

            if not ip:
                logging.info("%s - No IP for '%s' found" % (self.client_address[0], question.qname[:-1]))
                dnsQueryResponse = dnsQuery.response(dns.Rcode.NameError, question)
            else:
                logging.info("%s - Found IP '%s' for '%s'" % (self.client_address[0], ip, question.qname[:-1]))
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
            except select.error:
                pass # ignoring it, happens when select call will be interrupted by user change
            except:
                logging.exception("Unhandled exception in DNS server loop")
    
    def stop(self):
        self.cancel = True

