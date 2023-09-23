#!/usr/bin/env python

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

import logging.config
import sys

from mpddns.catalog import Catalog
from mpddns.config import Config, ConfigError
from mpddns.dnsserver import DnsServer
from mpddns.updateserver import UpdateServer
from mpddns.httpupdateserver import HTTPUpdateServer

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console"
        }
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": [
                "console"
            ]
        }
    }
}

logger = logging.getLogger(__name__)


class Main(object):
    def __init__(self):
        self.http_update_srv = None
        self.update_srv = None
        self.dns_srv = None

    def start(self):
        try:
            self.config = Config()
        except ConfigError as e:
            sys.stderr.write("Error while reading config file - %s\n" % str(e))
        else:
            self.run()

    def run(self):
        logging.config.dictConfig(LOG_CONFIG)

        logger.info("Starting mpddns server")

        catalog = Catalog(self.config.catalog, self.config.cache_file)

        self.dns_srv = DnsServer(self.config.dns_server, catalog)
        self.dns_srv.start()

        if self.config.update_server:
            self.update_srv = UpdateServer(self.config.update_server, catalog)
            self.update_srv.start()
        else:
            self.update_srv = None

        if self.config.http_update_server:
            self.http_update_srv = HTTPUpdateServer(self.config.http_update_server, catalog)
            self.http_update_srv.start()
        else:
            self.http_update_srv = None

        try:
            self.dns_srv.join()

            if self.config.update_server:
                self.update_srv.join()

            if self.config.http_update_server:
                self.http_update_srv.join()

        except KeyboardInterrupt:
            self.dns_srv.stop()

            if self.config.update_server:
                self.update_srv.stop()

            if self.config.http_update_server:
                self.http_update_srv.stop()

        logger.info("Stopping mpddns server")


if __name__ == "__main__":
    Main().start()
