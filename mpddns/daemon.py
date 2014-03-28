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

import fcntl
import logging
import os.path
import signal
import sys


class Daemon(object):
    def __init__(self, pidfile=None):
        self.lockfile = None
        self.pidfile = pidfile

    def __enter__(self):
        if not self.check_lock_file():
            raise RuntimeError("There is already an instance of this process running")

        self.daemonize()
        self.write_pid_file()

    def __exit__(self, exc_type, exc_value, traceback_):
        try:
            if self.pidfile and self.lockfile:
                self.lockfile.close()
                os.remove(self.pidfile)
        except:
            pass

    def daemonize(self):
        # http://www.microhowto.info/howto/cause_a_process_to_become_a_daemon.html

        try:
            if os.fork() > 0:
                os._exit(0)
        except OSError, e:
            logging.critical("fork() failed: %s (%s)\n" % (e.strerror, e.errno))
            os._exit(1)

        os.setsid()

        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        try:
            if os.fork() > 0:
                os._exit(0)
        except OSError, e:
            logging.critical("fork() failed: %s (%s)\n" % (e.strerror, e.errno))
            os._exit(1)

        os.chdir("/")
        os.umask(0)

        sys.stdout.flush()
        sys.stderr.flush()
        si = file("/dev/null", "r")
        so = file("/dev/null", "a")
        se = file("/dev/null", "a+", 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def check_lock_file(self):
        if self.pidfile and os.path.isfile(self.pidfile):
            with open(self.pidfile, "r") as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except IOError:
                    return False  # file is locked => another process is running
        return True

    def write_pid_file(self):
        if self.pidfile:
            try:
                self.lockfile = open(self.pidfile, "w+")
                fcntl.flock(self.lockfile, fcntl.LOCK_EX)
                self.lockfile.write("%s" % str(os.getpid()))
                self.lockfile.flush()
            except:
                logging.error("Writing pid file %s failed" % self.pidfile)
