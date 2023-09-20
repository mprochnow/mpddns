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

import argparse
import configparser


class ConfigError(Exception):
    pass


class Config:
    def __init__(self):
        self.catalog = None
        self.update_server = None
        self.dns_server = None
        self.cache_file = None
        self.config_file = None
        self.http_update_server = None
        self.parse_cmd_line()
        self.parse_config_file()

    def parse_cmd_line(self):
        parser = argparse.ArgumentParser(description="A simple dynamic DNS")
        parser.add_argument("-c",
                            metavar="<config-file>",
                            help="config file (default: /etc/mpddns/mpddns.conf)",
                            default="/etc/mpddns/mpddns.conf")
        results = parser.parse_args()

        self.config_file = results.c

    def parse_config_file(self):
        parser = configparser.ConfigParser()

        try:
            if not parser.read(self.config_file):
                raise ConfigError("Unable to open file '%s'" % self.config_file)
        except configparser.Error:
            raise ConfigError("File '%s' seems to be an invalid config file" % self.config_file)

        self.cache_file = parser.get("mpddns", "cache_file", fallback="/tmp/mpddns.cache")

        self.dns_server = (parser.get("dns_server", "bind", fallback="0.0.0.0"),
                           parser.getint("dns_server", "port", fallback=53))

        if parser.getboolean("update_server", "enabled", fallback=True):
            self.update_server = (parser.get("update_server", "bind", fallback="0.0.0.0"),
                                  parser.getint("update_server", "port", fallback=7331))
        else:
            self.update_server = None

        if parser.getboolean("http_update_server", "enabled", fallback=False):
            self.http_update_server = (parser.get("http_update_server", "bind", fallback="0.0.0.0"),
                                       parser.getint("http_update_server", "port", fallback=8000))
        else:
            self.http_update_server = None

        if not self.update_server and not self.http_update_server:
            raise ConfigError("At least one update server variant needs to be activated")

        if not parser.has_section("catalog"):
            raise ConfigError("Section 'catalog' not given")

        catalog_items = parser.items("catalog")
        if not catalog_items:
            raise ConfigError("Section 'catalog' is empty")

        self.catalog = {}
        for domain, secret in catalog_items:
            if not secret:
                raise ConfigError("No password for domain '%s' given" % domain)

            self.catalog[domain] = secret
