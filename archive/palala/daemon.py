#!/usr/bin/env python

import sys, os
import pwd
import time
import signal


#
# daemon class extracted from ll-core-1.9.1 library downloaded from
# http://www.livinglogic.de/Python/core/Download.html
# edited in minor ways to fit the bot code
#
# The following is the original copyright and license file:
#
    ## Copyright 2007 by LivingLogic AG, Bayreuth/Germany.
    ## Copyright 2007 by Walter D\xc3rwald
    ##
    ## All Rights Reserved
    ##
    ## All Rights Reserved
    ##
    ## Permission to use, copy, modify, and distribute this software and its documentation
    ## for any purpose and without fee is hereby granted, provided that the above copyright
    ## notice appears in all copies and that both that copyright notice and this permission
    ## notice appear in supporting documentation, and that the name of LivingLogic AG or
    ## the author not be used in advertising or publicity pertaining to distribution of the
    ## software without specific, written prior permission.
    ##
    ## LIVINGLOGIC AG AND THE AUTHOR DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
    ## INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL
    ## LIVINGLOGIC AG OR THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
    ## DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
    ## IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR
    ## IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

class Daemon(object):
    """
    The <class>Daemon</class> class provides methods for <pyref method="start">starting</pyref>
    and <pyref method="stop">stopping</pyref> a daemon process as well as
    <pyref method="service">handling command line arguments</pyref>.
    """
    def __init__(self, log=None, pidfile=None, user=None, group=None, sigterm=None, stdout='/dev/null', stderr='/dev/null', stdin='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.user = user
        self.group = group
        self.sigterm = sigterm
        self.log = log

    def openstreams(self):
        """
        Open the standard file descriptors stdin, stdout and stderr as specified
        in the constructor.
        """
        si = open(self.stdin, "r")
        os.dup2(si.fileno(), sys.stdin.fileno())

        if self.log is not None:
            os.dup2(self.log.stream.fileno(), sys.stdout.fileno())
            os.dup2(self.log.stream.fileno(), sys.stderr.fileno())
        else:
            so = open(self.stdout, "a+")
            se = open(self.stderr, "a+", 0)
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

    def handlesighup(self, signum, frame):
        """
        Handle a <lit>SIG_HUP</lit> signal: Reopen standard file descriptors.
        """
        self.openstreams()

    def handlesigterm(self, signum, frame):
        """
        Handle a <lit>SIG_TERM</lit> signal: Remove the pid file and exit.
        """
        if self.pidfile is not None:
            try:
                os.remove(self.pidfile)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
        sys.exit(0)

    def switchuser(self, user, group):
        """
        Switch the effective user and group. If <arg>user</arg> is <lit>None</lit>
        and <arg>group</arg> is nothing will be done. <arg>user</arg> and <arg>group</arg>
        can be an <class>int</class> (i.e. a user/group id) or <class>str</class>
        (a user/group name).
        """
        if group is not None:
            if isinstance(group, basestring):
                group = grp.getgrnam(group).gr_gid
            os.setegid(group)
        if user is not None:
            if isinstance(user, basestring):
                user = pwd.getpwnam(user).pw_uid
            os.seteuid(user)
            if "HOME" in os.environ:
                os.environ["HOME"] = pwd.getpwuid(user).pw_dir

    def start(self):
        """
        Daemonize the running script. When this method returns the process is
        completely decoupled from the parent environment.
        """
        # Finish up with the current stdout/stderr
        sys.stdout.flush()
        sys.stderr.flush()

        # Do first fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.stdout.close()
                sys.exit(0) # Exit first parent
        except OSError, exc:
            sys.exit("%s: fork #1 failed: (%d) %s\n" % (sys.argv[0], exc.errno, exc.strerror))

        # Decouple from parent environment
        os.chdir("/")
        os.umask(0)
        os.setsid()

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.stdout.close()
                sys.exit(0) # Exit second parent
        except OSError, exc:
            sys.exit("%s: fork #2 failed: (%d) %s\n" % (sys.argv[0], exc.errno, exc.strerror))

        # Now I am a daemon!

        # Switch user
        self.switchuser(self.user, self.group)

        # Redirect standard file descriptors (will belong to the new user)
        self.openstreams()

        # Write pid file (will belong to the new user)
        if self.pidfile is not None:
            open(self.pidfile, "wb").write(str(os.getpid()))

        # Reopen file descriptions on SIGHUP
        signal.signal(signal.SIGHUP, self.handlesighup)

        # Remove pid file and exit on SIGTERM
        signal.signal(signal.SIGTERM, self.sigterm) #self.handlesigterm)

    def stop(self):
        """
        Send a <lit>SIGTERM</lit> signal to a running daemon. The pid of the
        daemon will be read from the pidfile specified in the constructor.
        """
        if self.pidfile is None:
            sys.exit("no pidfile specified")
        try:
            pidfile = open(self.pidfile, "rb")
        except IOError, exc:
            sys.exit("can't open pidfile %s: %s" % (self.pidfile, str(exc)))
        data = pidfile.read()
        try:
            pid = int(data)
        except ValueError:
            sys.exit("mangled pidfile %s: %r" % (self.pidfile, data))
        os.kill(pid, signal.SIGTERM)

    def service(self, args=None):
        """
        <par>Handle command line arguments and start or stop the daemon accordingly.</par>

        <par><arg>args</arg> must be a list of command line arguments (including the
        program name in <lit>args[0]</lit>). If <arg>args</arg> is <lit>None</lit>
        or unspecified <lit>sys.argv</lit> is used.</par>

        <par>The return value is true, if <option>start</option> has been specified
        as the command line argument, i.e. if the daemon should be started.</par>
        """
        if args is None:
            args = sys.argv
        if len(args) < 2 or args[1] not in ("start", "stop"):
            sys.exit("Usage: %s (start|stop)" % args[0])
        if args[1] == "start":
            self.start()
            return True
        else:
            self.stop()
            return False

