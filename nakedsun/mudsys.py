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
This module provides a great deal of the MUD system functions, including
functions for account creation, logging in, logging out, and shutting the
server down.
"""

###############################################################################
# Imports
###############################################################################

from . import account
from . import bitvectors
from . import char
from . import mudsock
from . import obj
from . import room

from . import logger as log

###############################################################################
# Storage and Constants
###############################################################################

pymodules = {}

###############################################################################
# The Copyover Exception
###############################################################################

class SystemCopyover(SystemExit):
    """
    This exception, a subclass of SystemExit, instructs the server to perform a
    copyover.
    """
    pass

###############################################################################
# Public Functions
###############################################################################

@log.implement
def account_creating(name):
    """
    Returns True if an account with the provided name has been created but not
    yet been saved.
    """
    return False

@log.implement
def account_exists(name):
    """
    Returns True if an account with the provided name exists.
    """
    return False

def add_acct_method(name, method):
    """
    Add a function, property, or other attribute to the
    :class:`account.Account` class.

    .. note::

        This method exists for compatibility with NakedMud and doesn't do
        anything special. You may simply modify the :class:`account.Account`
        class directly.
    """
    setattr(account.Account, name, method)

def add_char_method(name, method):
    """
    Add a function, property, or other attribute to the
    :class:`char.Char` class.

    .. note::

        This method exists for compatibility with NakedMud and doesn't do
        anything special. You may simply modify the :class:`char.Char`
        class directly.
    """
    setattr(char.Char, name, method)

@log.implement
def add_cmd(*args):
    pass

@log.implement
def add_cmd_check(*args):
    pass

@log.implement
def set_cmd_move(*args):
    pass

@log.implement
def register_dflt_move_cmd(*args):
    pass

@log.implement
def register_move_check(*args):
    pass


def add_exit_method(name, method):
    """
    Add a function, property, or other attribute to the
    :class:`exit.Exit` class.

    .. note::

        This method exists for compatibility with NakedMud and doesn't do
        anything special. You may simply modify the :class:`exit.Exit`
        class directly.
    """
    pass

def add_obj_method(name, method):
    """
    Add a function, property, or other attribute to the
    :class:`obj.Obj` class.

    .. note::

        This method exists for compatibility with NakedMud and doesn't do
        anything special. You may simply modify the :class:`obj.Obj`
        class directly.
    """
    setattr(obj.Obj, name, method)

def add_room_method(name, method):
    """
    Add a function, property, or other attribute to the
    :class:`room.Room` class.

    .. note::

        This method exists for compatibility with NakedMud and doesn't do
        anything special. You may simply modify the :class:`room.Room`
        class directly.
    """
    setattr(room.Room, name, method)

def add_sock_method(name, method):
    """
    Add a function, property, or other attribute to the
    :class:`mudsock.Mudsock` class.

    .. note::

        This method exists for compatibility with NakedMud and doesn't do
        anything special. You may simply modify the :class:`mudsock.Mudsock`
        class directly.
    """
    setattr(mudsock.Mudsock, name, method)

def create_bit(bitvector, *bits):
    """ See :func:`bitvectors.create_bitvector`. """
    return bitvectors.create_bitvector(bitvector, *bits)

def create_bitvector(bitvector, *bits):
    """ See :func:`bitvectors.create_bitvector`. """
    return bitvectors.create_bitvector(bitvector, *bits)
