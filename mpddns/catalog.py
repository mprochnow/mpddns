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

import json
import logging


class CatalogEntry:
    def __init__(self, password):
        self.password = password
        self.ip = None


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
        if entry and entry.ip != ip:
            entry.ip = ip
            logging.info("Updated '%s' with '%s'" % (domain, ip))

            try:
                with open(self.cacheFile, "w") as f:
                    json.dump({domain: entry.ip for domain, entry in self.catalog.iteritems()}, f)
            except:
                logging.exception("Unhandled exception while writing cache file")

    def get_ip(self, domain):
        entry = self.catalog.get(domain.lower())
        if entry:
            return entry.ip
        return None

    def get_password(self, domain):
        entry = self.catalog.get(domain.lower())
        if entry:
            return entry.password
        return None
