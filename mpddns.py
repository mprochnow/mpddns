#!/usr/bin/env python

import grp
import logging.config
import os
import pwd
import signal
import sys

from mpddns.catalog import Catalog
from mpddns.config import Config, ConfigException
from mpddns.daemon import Daemon
from mpddns.dnsserver import DnsServer
from mpddns.updateserver import UpdateServer
from mpddns.httpupdateserver import HTTPUpdateServer

LOG_CONFIG = {"version": 1,
              "disable_existing_loggers": False,
              "handlers": {"default": {"class": "logging.StreamHandler"},
                           "syslog": {"class": "logging.handlers.SysLogHandler",
                                      "address": "/dev/log",
                                      "facility": "daemon"}},
              "loggers": {"": {"level": "DEBUG",
                               "handlers": ["default"]}}}

class Main(object):
    def __init__(self):
        try:
            self.config = Config()
        except ConfigException, e:
            sys.stderr.write('Error in config file - %s\n' % str(e))
    
        logging.config.dictConfig(LOG_CONFIG)

    def start(self):
        try:
            with Daemon(self.config.pid_file):
                self.run()
        except RuntimeError, e:
            sys.stderr.write('%s' % str(e))
    
    def run(self):
        try:
            logging.info('Starting mpddns server (pid: %s)' % os.getpid())

            catalog = Catalog(self.config.catalog, self.config.cache_file)

            self.dnsSrv = DnsServer(self.config.dns_server, catalog)
            self.dnsSrv.start()

            if self.config.update_server:
                self.updateSrv = UpdateServer(self.config.update_server, catalog)
                self.updateSrv.start()
            else:
                self.updateSrv = None

            if self.config.http_update_server:
                self.httpUpdateSrv = HTTPUpdateServer(self.config.http_update_server, catalog)
                self.httpUpdateSrv.start()
            else:
                self.httpUpdateSrv = None

            self.changeUserGroup(self.config.user, self.config.group)

            signal.signal(signal.SIGTERM, self.handleSignals)
            signal.pause()

            logging.info('Stopping mpddns server')
        except:
            logging.exception("Unhandled exception during start-up")

    def handleSignals(self, signum, frame):
        self.dnsSrv.stop()
        if self.updateSrv:
            self.updateSrv.stop()
        if self.httpUpdateSrv:
            self.httpUpdateSrv.stop()

    def changeUserGroup(self, user='nobody', group='nogroup'):
        if user and group:
            if os.getuid() != 0:
                logging.error("Not running as root, cannot change user/group")
                return

            try:
                uid = pwd.getpwnam(user).pw_uid
                gid = grp.getgrnam(group).gr_gid
            except KeyError:
                logging.error("User %s or group %s not found, will not change user/group" % (user, group))
                return

            try:
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)
            except OSError, e:
                logging.error("An error occurred while changing user/group - %s (%d)" % (e.strerror, e.errno))
                return

            logging.info("Changed user/group to %s/%s" % (user, group))

if __name__ == '__main__':
    Main().start()
