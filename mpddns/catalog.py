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

import json
import logging

log = logging.getLogger(__name__)


class CatalogEntry:
    def __init__(self, password):
        self.password = password
        self.ip = None


class Catalog:
    def __init__(self, data, cache_file):
        self.catalog = {}
        self.cache_file = cache_file

        for domain, password in data.items():
            self.catalog[domain] = CatalogEntry(password)

        cache_data = {}
        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.warning(f"Error while opening '{cache_file}': {e}")

        for domain, ip in cache_data.items():
            self.update_ip(domain, ip)

    def update_ip(self, domain, ip):
        domain = domain.lower()

        entry = self.catalog.get(domain)
        if entry and entry.ip != ip:
            entry.ip = ip
            log.info("Updated '%s' with '%s'" % (domain, ip))

            try:
                with open(self.cache_file, "w") as f:
                    json.dump({domain: entry.ip for domain, entry in self.catalog.items()}, f)
            except (OSError, json.JSONDecodeError):
                log.exception("Unhandled exception while writing cache file")

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
