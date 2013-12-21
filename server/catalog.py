from syslog import syslog

class CatalogEntry:
    def __init__(self, password):
        self.password = password
        self.ip = None

    def updateIp(self, ip):
        self.ip = ip

    def getIp(self):
        return self.ip

    def getPassword(self):
        return self.password

class Catalog:
    def __init__(self, data):
        self.catalog = {}

        for domain, config in data.iteritems():
            if config.get("password"):
                self.catalog[domain] = CatalogEntry(config["password"])
            else:
                syslog("'%s' has no password given" % domain)

    def updateIp(self, domain, ip):
        entry = self.catalog.get(domain)
        if entry and entry.getIp() != ip:
            entry.updateIp(ip)

            syslog("Updated '%s' with '%s'" % (domain, ip))

    def getIp(self, domain):
        entry = self.catalog.get(domain)
        if entry:
            return entry.getIp()
        return None

    def getPassword(self, domain):
        entry = self.catalog.get(domain)
        if entry:
            return entry.getPassword()
        return None
