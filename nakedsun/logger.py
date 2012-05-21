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
This module creates a centralized logger for NakedSun and initializes the
logging system. It also provides a logging formatter with support for ANSI
color sequences to make logs a bit prettier in the console.
"""

###############################################################################
# Imports
###############################################################################

import logging
import logging.handlers
import os
import subprocess
import sys
import time

###############################################################################
# Storage and Constants
###############################################################################

_log = None
_width = 80

critical = debug = error = exception = info = warning = log = None

DEPRECIATED = logging.INFO - 1
LINE = logging.INFO + 1
NAKED = LINE + 1
MUD = NAKED + 1
TODO = MUD + 1

logging.addLevelName(LINE, "---------")
logging.addLevelName(NAKED, "!!NAKED!!")
logging.addLevelName(MUD, "MUD")
logging.addLevelName(TODO, "TO-DO")

COLORS = {
    'CRITICAL'  : 5,
    'DEBUG'     : 4,
    'ERROR'     : 1,
    '---------' : 7,
    'INFO'      : 7,
    'MUD'       : 2,
    '!!NAKED!!' : 2,
    'TO-DO'     : 6,
    'WARNING'   : 3
    }

###############################################################################
# ColoredFormatter Class
###############################################################################

class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, datefmt=None, use_color=True):
        super(ColoredFormatter, self).__init__(msg, datefmt)
        self.use_color = use_color

    def format(self, record):
        level = record.levelname
        if self.use_color and level in COLORS:
            spacing = " " * (9 - len(level))
            level_color = "\x1B[1;%dm%s%s\x1B[0m" % (30 + COLORS[level],
                                                     spacing, level)
            record.levelname = level_color
        return logging.Formatter.format(self, record)

###############################################################################
# Initialization
###############################################################################

def initialize(use_color, level, path, logger=''):
    """
    Initialize NakedSun's logger.
    """
    global _log
    global _width
    global critical
    global debug
    global error
    global exception
    global info
    global warning
    global log

    ## Parse the Level
    if isinstance(level, basestring):
        if level.upper() in dir(logging):
            level = getattr(logging, level.upper())
        else:
            try:
                level = int(level)
            except (TypeError, ValueError):
                level = logging.INFO

    ## Colorization

    colorama_warning = False

    if sys.platform == 'win32':
        # As Windows, for some reason known only to Microsoft, refuses to
        # support ANSI escape codes in their consoles, we'll try to import a
        # module called colorama that intercepts those codes sent to sys.stdout
        # and translates them into system calls.
        try:
            from colorama import init
            init()
        except ImportError:
            # Set a flag for later since the log isn't set up yet.
            colorama_warning = True

    ## Console Width

    try:
        process = subprocess.Popen(['resize'], stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)
        out, _ = process.communicate()
        _width = int(out[8:out.find(';')]) or 80
    except (OSError, ValueError):
        _width = 80

    ## The Logger

    # We're using the root logger by default because why not? NakedSun is
    # meant to be the core application.
    _log = logging.getLogger(logger)

    # Set useful stuff.
    critical = _log.critical
    debug = _log.debug
    error = _log.error
    exception = _log.exception
    info = _log.info
    log = _log.log
    warning = _log.warning

    # Set the logging level.
    _log.setLevel(level)

    ## The Console Handler

    # Create the stream handler and set its level too.
    console = logging.StreamHandler()
    console.setLevel(level)

    # Are we using color? Make sure we are.
    if use_color:
        if sys.platform == 'win32':
            use_color = not colorama_warning
        else:
            use_color = sys.stdout.isatty()

    # Create a formatter.
    if use_color:
        formatter = ColoredFormatter(
            (u"\x1B[1;30m[%(levelname)-20s\x1B[1;30m]\x1B[0m %(asctime)s "
             u"\x1B[1;37m%(message)s\x1B[0m"),
            u"%H:%M:%S"
            )
    else:
        formatter = logging.Formatter(
            u"[%(levelname)-9s] %(asctime)s %(message)s",
            u"%H:%M:%S"
            )

    console.setFormatter(formatter)
    _log.addHandler(console)
    
    ## The File Handler

    # Ensure that the log directory exists.
    if not os.path.exists(path) or not os.path.isdir(path):
        error(u"Unable to store log files in %r." % os.path.realpath(path))
    else:
        file = logging.handlers.TimedRotatingFileHandler(
                    filename    = os.path.join(path, "log"),
                    when        = "midnight"
                    )
        file.setLevel(max(logging.INFO, level))

        formatter = logging.Formatter(
            u"%(asctime)s\t%(levelname)s\t%(message)s",
            u"%Y-%m-%d %H:%M:%S"
            )

        file.setFormatter(formatter)
        _log.addHandler(file)

    # Display a colorization warning if using Windows without colorama.
    if colorama_warning:
        warning(
            u"Log colorization has been disabled. Please install the "
            u"colorama module."
            )

###############################################################################
# Useful Functions
###############################################################################

def implement(func, last={}):
    """
    Log a simple to-do message, but keep it rate-limited to avoid spam.
    """
    last[func] = 0
    def wrapper(*args, **kwargs):
        now = time.time()
        if now - last[func] > 30:
            todo("Implement: %s.%s" % (func.__module__, func.func_name))
        last[func] = now
        return func(*args, **kwargs)
    return wrapper

def mud(msg, *a, **kw):
    log(MUD, msg, *a, **kw)

def naked(msg, *a, **kw):
    log(NAKED, msg, *a, **kw)

def todo(msg, *a, **kw):
    log(TODO, msg, *a, **kw)

def line():
    log(LINE, u"-" * (_width - 21))

shutdown = logging.shutdown
