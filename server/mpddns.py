#!/usr/bin/env python

import grp
import os
import pwd
import signal
import sys
import syslog
import traceback

from catalog import Catalog
from config import Config, ConfigException
from daemon import Daemon
from dnsserver import DnsServer
from updateserver import UpdateServer
from httpupdateserver import HTTPUpdateServer

class Main(object):
    def __init__(self):
        try:
            self.config = Config()
        except ConfigException, e:
            sys.stderr.write('Error in config file - %s\n' % str(e))
    
    def start(self):
        try:
            with Daemon(self.config.pid_file):
                self.run()
        except RuntimeError, e:
            sys.stderr.write('%s' % str(e))
    
    def run(self):
        try:
            syslog.syslog('Starting mpddns server (pid: %s)' % os.getpid())

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

            syslog.syslog('Stopping mpddns server')
        except:
            syslog.syslog(syslog.LOG_CRIT, traceback.format_exc())

    def handleSignals(self, signum, frame):
        self.dnsSrv.stop()
        if self.updateSrv:
            self.updateSrv.stop()
        if self.httpUpdateSrv:
            self.httpUpdateSrv.stop()

    def changeUserGroup(self, user='nobody', group='nogroup'):
        if user and group:
            if os.getuid() != 0:
                syslog.syslog(syslog.LOG_ERR, "Not running as root, cannot change user/group")
                return

            try:
                uid = pwd.getpwnam(user).pw_uid
                gid = grp.getgrnam(group).gr_gid
            except KeyError:
                syslog.syslog(syslog.LOG_ERR, "User %s or group %s not found, will not change user/group" % (user, group))
                return

            try:
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)
            except OSError, e:
                syslog.syslog(syslog.LOG_ERR, "An error occurred while changing user/group - %s (%d)" % (e.strerror, e.errno))
                return

            syslog.syslog("Changed user/group to %s/%s" % (user, group))

if __name__ == '__main__':
    syslog.openlog("mpddns")
    Main().start()
