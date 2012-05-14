###############################################################################
#
# Copyright 2012 Stendec <me@stendec.me>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
"""
This is the core of NakedSun where, among other things, the event loop is
entered when the MUD starts. The core is also responsible for setting up the
basic servers.
"""

###############################################################################
# Imports
###############################################################################

import os
import argparse
import signal
import sys

import pants

import nakedsun
import nakedsun.logger as log

do_uid = hasattr(os, "getuid")

###############################################################################
# The Signal Handler
###############################################################################

def signal_HUP(signum, frame):
    """
    If we catch a SIGHUP, the MUD should perform a copyover.
    """
    import nakedsun.mudsys
    raise nakedsun.mudsys.SystemCopyover

###############################################################################
# Helper Functions
###############################################################################

def assume_uid(uid, gid, umask):
    """
    Assume the given UID, GID, and UMASK.
    """
    log.todo(u"UID/GID/UMASK support.")

def inject(name, module):
    """
    Inject a module into sys.modules with the given name.
    """
    log.debug("Injecting %r into sys.modules as %r." % (module.__name__, name))
    sys.modules[name] = module

###############################################################################
# The Main Function
###############################################################################

def main():
    """
    Initialize everything and launch NakedSun. This method is in charge of
    parsing command line arguments, locating the MUD library, loading all the
    available modules, loading the world, etc.
    """

    ## Argument Parsing

    parser = argparse.ArgumentParser(
                prog="python -m nakedsun",
                description=nakedsun.__doc__,
                version="NakedSun %s" % nakedsun.version
                )
    
    # Basic Options
    
    parser.add_argument("--path", dest="lib", default="lib", metavar="PATH",
                        help="Load the MUD library from PATH.")
    parser.add_argument("--copyover", help=argparse.SUPPRESS)
    
    # Network Options
    group = parser.add_argument_group(
                u"Network Options",
                u"These options allow you to override the default listening "
                u"addresses for the server."
                )

    group.add_argument("-b", "--bind", dest="addr", default=None,
                    help=u"Bind the telnet server to the given ADDRESS:PORT.")
    group.add_argument("--http", dest="http_addr", default=None,
                    help=u"Bind the HTTP server to the given ADDRESS:PORT.")

    # Logging Options

    group = parser.add_argument_group(u"Logging Options")

    group.add_argument("-l", "--log", default="../log", metavar="PATH",
        help=u"Store log files at PATH, relative to the MUD library.")
    group.add_argument("--level", default="INFO",
        help=u"Only log messages of LEVEL or higher. (Default: INFO)")
    group.add_argument("--no-color", default=True, action="store_false",
        dest="color", help=u"Disable console output colorization.")

    # UID/GID Manipulation

    if do_uid:
        group = parser.add_argument_group(
            u"User/Group ID Manipulation",
            u"These options, if used, will be acted upon *immediately* before "
            u"entering the main event loop. This is slightly unsafe, since "
            u"any code in the MUD library will be executed before the new "
            u"user and/or group identity is assumed. However, this is "
            u"necessary to ensure the server is able to bind low ports on UNIX"
            u" systems as root. The provided values may be either names "
            u"or numbers. These values may also be set in the MUD's "
            u"configuration file.")

        group.add_argument("-u", "--user", help=u"Run as the specified user.")
        group.add_argument("-g", "--group",
            help=u"Run as the specified group.")
        group.add_argument("--umask", help=u"Use the provided umask.")
        group.add_argument("--early", default=False, action="store_true",
            help=u"Assume the new identity early, before executing any code "
                 u"from the MUD library.")

    # Finally, parse the arguments.
    args = parser.parse_args()

    ## Logging

    log.initialize(args.color, True, os.path.join(args.lib, args.log))
    log.naked(u"NakedSun v%s by Stendec <me@stendec.me>" % nakedsun.version)

    ## Enter the MUD Library

    path = os.path.realpath(args.lib)
    if not os.path.exists(path) or not (
            os.path.exists(os.path.join(path, 'muddata')) or
            os.path.exists(os.path.join(path, 'config'))):
        log.error(u"Cannot find the MUD library at %r." % path)
        log.shutdown()
        sys.exit(1)

    if path != os.getcwd():
        log.info(u"Changing working directory to %r." % path)
        os.chdir(path)

    ## Initialize Basic Functionality
    
    # Inject our modules in preparation for loading the MUD library.
    for module in ("bitvectors", "event", "hooks"):
        inject(module, getattr(nakedsun, module))

    ## Load Configuration

    log.info(u"Loading MUD configuration from file.")
    log.todo(u"Actually load the configuration.")

    ## Networking Initialization

    log.info(u"Initializing the network.")
    log.todo(u"Actually initialize the network.")

    ## Early UID/GID Manipulation

    if do_uid and args.early:
        assume_uid(args.user, args.group, args.umask)

    ## NakedMud Compatibility

    log.todo(u"Load NakedMud Compatibility Layer.")

    ## MUD Library Initialization

    log.todo(u"Execution of MUD library.")

    ## Copyover Recovery

    log.todo("Copyover Recovery.")

    ## Register Signals

    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_HUP)

    ## Late UID/GID Manipulation

    if do_uid and not args.early:
        assume_uid(args.user, args.group, args.umask)

    ## The Event Loop
    
    log.info(u"Entering the game loop.")
    log.line()

    begin_copyover = False

    try:
        pants.engine.start()
    except nakedsun.mudsys.SystemCopyover:
        begin_copyover = True
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print ''

    log.line()

    if begin_copyover:
        log.todo("Copyover.")

    ## Cleanup

    nakedsun.hooks.run("shutdown")

    log.info(u"Exiting normally.")
    log.shutdown()
    sys.exit(0)
