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

import grp
import logging.config
import os
import pwd
import signal
import sys

from catalog import Catalog
from config import Config, ConfigError
from daemon import Daemon
from dnsserver import DnsServer
from updateserver import UpdateServer
from httpupdateserver import HTTPUpdateServer

LOG_CONFIG = {"version": 1,
              "disable_existing_loggers": False,
              "formatters": {"syslog": {"format": "%(name)s[%(process)d]: %(message)s"}},
              "handlers": {"syslog": {"class": "logging.handlers.SysLogHandler",
                                      "address": "/dev/log",
                                      "facility": "daemon",
                                      "formatter": "syslog"}},
              "loggers": {"mpddns": {"level": "DEBUG",
                                     "handlers": ["syslog"]}}}

logger = logging.getLogger("mpddns")


class Main(object):
    def __init__(self):
        pass

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

    def handleSignals(self, signum, frame):
        self.dns_srv.stop()
        if self.update_srv:
            self.update_srv.stop()
        if self.http_update_srv:
            self.http_update_srv.stop()


if __name__ == "__main__":
    Main().start()
