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
This module contains miscellaneous utility functions for the MUD.
"""

###############################################################################
# Imports
###############################################################################

import os

from . import logger as log

###############################################################################
# Storage and Constants
###############################################################################

_globals = {}

###############################################################################
# Public Functions
###############################################################################

def erase_global(name):
    """ Delete a value from the global variable table. """
    if name in _globals:
        del _globals[name]

@log.implement
def expand_text(text, environ=None, newline=False):
    """
    Process the given text with NakedSun's template system. By default, a
    NakedMud-compatible template system is used. If an environment is not
    provided, an empty environment will be used. If newline is True, a line
    return will be appended to the text.
    """

    if newline:
        text += "\r\n"

    return text

@log.implement
def extract(thing):
    """ Extract an object, character, room, etc. from the game. """
    pass

@log.implement
def format_string(text, indent=True, width=80):
    """
    Format a block of text to fit the specified width, possibly
    indenting paragraphs.
    """
    return text

def get_global(name):
    """
    Return a non-persistent global variable, or None if it doesn't exist.
    """
    return _globals.get(name, None)

def get_greeting(cache=True):
    """
    Get the MUD's greeting from ``lib/txt/greeting`` and return it as a string.
    The file will be cached to memory by default. Set cache to False to avoid
    using the cached version.
    """
    if not cache or not "greeting" in _globals:
        with open(os.path.join("txt", "greeting"), "rb") as fl:
            _globals["greeting"] = fl.read()
    return _globals["greeting"]

def get_motd(cache=True):
    """
    Get the MUD's message of the day from ``lib/txt/motd`` and return it as a
    string. The file will be cached to memory by default. Set cache to False to
    avoid using the cached version.
    """
    if not cache or not "motd" in _globals:
        with open(os.path.join("txt", "motd"), "rb") as fl:
            _globals["motd"] = fl.read()
    return _globals["motd"]

def ite(statement, if_true, if_false):
    """
    This function is depreciated and only included for NakedMud compatibility.
    """
    log.warning("Depreciated: Don't use mud.ite.")
    return if_true if statement else if_false

@log.implement
def keys_equal(key1, key2):
    """
    Returns whether the provided world database keys are equal, relative to the
    locale (if any) of the currently running script.
    """
    return key1 == key2

def log_string(message, level=log.MUD):
    """
    Record a message to the MUD's log. This function exists for compatibility
    with NakedMud, and has been superseded by the logging module. Just log
    normally and it should work fine.
    """
    log.log(level, message)

def set_global(name, val):
    """ Set a non-persistent global variable. """
    _globals[name] = val
