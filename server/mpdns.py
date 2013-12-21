#!/usr/bin/env python

import signal
import syslog
import traceback

from catalog import Catalog
from config import Config, ConfigException
from daemon import DaemonBase
from dnsserver import DnsServer
from updateserver import UpdateServer

class Daemon(DaemonBase):
    def run(self):
        try:
            syslog.openlog("mpdns")
            catalog = Catalog(self.config.catalog)

            self.dnsSrv = DnsServer((self.config.dnsBind, self.config.dnsPort), catalog)
            self.updateSrv = UpdateServer((self.config.updateBind, self.config.updatePort), catalog)

            self.dnsSrv.start()
            self.updateSrv.start()

            # TODO find something less ugly
            # time.sleep(1) # give servers time to initialize
            # self.dropPrivileges()

            signal.signal(signal.SIGTERM, self.handleSignals)
            signal.pause()
        except:
            syslog.syslog(traceback.format_exc())
    
    def handleSignals(self, signum, frame):
        self.updateSrv.stop()
        self.dnsSrv.stop()

    # http://stackoverflow.com/questions/2699907/dropping-root-permissions-in-python/2699996#2699996
    def dropPrivileges(self, uidName='nobody', gidName='nogroup'):
        import os, pwd, grp

        if os.getuid() != 0:
            return # We're not root so, like, whatever dude

        # Get the uid/gid from the name
        uid = pwd.getpwnam(uidName).pw_uid
        gid = grp.getgrnam(gidName).gr_gid

        # Remove group privileges
        os.setgroups([])

        # Try setting the new uid/gid
        os.setgid(gid)
        os.setuid(uid)

        # Ensure a very conservative umask
        os.umask(077)

def main():
    try:
        config = Config()

        d = Daemon(config.pidFile)
        d.config = config
        d.start()
    except ConfigException, e:
        print "Error in config file:", str(e)
    except Exception, e:
        print "Runtime exception:", str(e)
    

if __name__ == '__main__':
    main()
