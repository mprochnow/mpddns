#!/usr/bin/env python

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
        except ConfigError, e:
            sys.stderr.write("Error while reading config file - %s\n" % str(e))
        else:
            try:
                with Daemon(self.config.pid_file):
                    self.run()
            except RuntimeError, e:
                sys.stderr.write('%s' % str(e))

    def run(self):
        try:
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

            self.change_user_group(self.config.user, self.config.group)

            signal.signal(signal.SIGTERM, self.handleSignals)
            signal.pause()

            logger.info("Stopping mpddns server")
        except:
            logger.exception("Unhandled exception during start-up")

    def handleSignals(self, signum, frame):
        self.dns_srv.stop()
        if self.update_srv:
            self.update_srv.stop()
        if self.http_update_srv:
            self.http_update_srv.stop()

    def change_user_group(self, user="nobody", group="nogroup"):
        if user and group:
            if os.getuid() != 0:
                logger.error("Not running as root, cannot change user/group")
                return

            try:
                uid = pwd.getpwnam(user).pw_uid
                gid = grp.getgrnam(group).gr_gid
            except KeyError:
                logger.error("User %s or group %s not found, will not change user/group" % (user, group))
                return

            try:
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)
            except OSError, e:
                logger.error("An error occurred while changing user/group - %s (%d)" % (e.strerror, e.errno))
                return

            logger.info("Changed user/group to %s/%s" % (user, group))

if __name__ == "__main__":
    Main().start()
