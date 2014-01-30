import syslog
import json
import traceback

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
    def __init__(self, data, cacheFile):
        self.catalog = {}
        self.cacheFile = cacheFile
        
        cacheData = {}
        try:
            with open(self.cacheFile, 'r') as f:
                cacheData = json.load(f)
        except:
            pass

        for domain, config in data.iteritems():
            domain = domain.lower()

            if config.get("password"):
                self.catalog[domain] = CatalogEntry(config["password"])

                if domain in cacheData:
                    self.catalog[domain].updateIp(cacheData[domain])
            else:
                syslog.syslog("'%s' has no password given" % domain)

    def updateIp(self, domain, ip):
        domain = domain.lower()
        entry = self.catalog.get(domain)
        if entry is None:
            return False

        if entry.getIp() == ip:
            return True
        
        entry.updateIp(ip)
        syslog.syslog("Updated '%s' with '%s'" % (domain, ip))

        try:
            with open(self.cacheFile, 'w') as f:
                json.dump({domain: entry.getIp() for domain, entry in self.catalog.iteritems()}, f)
        except:
            syslog.syslog(syslog.LOG_ERR, traceback.format_exc())

        return True

    def getIp(self, domain):
        domain = domain.lower()
        entry = self.catalog.get(domain)
        if entry:
            return entry.getIp()
        return None

    def getPassword(self, domain):
        domain = domain.lower()
        entry = self.catalog.get(domain)
        if entry:
            return entry.getPassword()
        return None
