import json
import logging

class CatalogEntry:
    def __init__(self, password):
        self.password = password
        self.ip = None

    def update_ip(self, ip):
        self.ip = ip

    def get_ip(self):
        return self.ip

    def get_password(self):
        return self.password

class Catalog:
    def __init__(self, data, cacheFile):
        self.catalog = {}
        self.cacheFile = cacheFile
        
        for domain, password in data.iteritems():
            self.catalog[domain] = CatalogEntry(password)

        cacheData = {}
        try:
            with open(self.cacheFile, "r") as f:
                cacheData = json.load(f)
        except:
            pass

        for domain, ip in cacheData.iteritems():
            self.update_ip(domain, ip)

    def update_ip(self, domain, ip):
        domain = domain.lower()

        entry = self.catalog.get(domain)
        if entry and entry.get_ip() != ip:
            entry.update_ip(ip)
            logging.info("Updated '%s' with '%s'" % (domain, ip))

            try:
                with open(self.cacheFile, "w") as f:
                    json.dump({domain: entry.get_ip() for domain, entry in self.catalog.iteritems()}, f)
            except:
                logging.exception("Unhandled exception while writing cache file")

    def get_ip(self, domain):
        entry = self.catalog.get(domain.lower())
        if entry:
            return entry.get_ip()
        return None

    def get_password(self, domain):
        entry = self.catalog.get(domain.lower())
        if entry:
            return entry.get_password()
        return None
