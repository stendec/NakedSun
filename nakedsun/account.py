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
This module contains the account class that represents player accounts within
the MUD server.
"""

###############################################################################
# Imports
###############################################################################

import weakref

from . import auxiliary
from . import logger as log
from . import utils

###############################################################################
# Storage
###############################################################################

_accounts = weakref.WeakValueDictionary()

###############################################################################
# Account Class
###############################################################################

@auxiliary.register("account")
class Account(auxiliary.AuxiliaryBase):
    """
    This class represents a player account in NakedSun and maintains a list of
    characters associated with the account. Password functionality, for
    security, is *not* handled by this class. See
    :func:`mudsys.password_matches` and :func:`mudsys.set_password` for working
    with passwords.
    """

    def __init__(self, name):
        """
        Initialize the named account.
        """


    ##### Character Management ################################################

    @log.implement
    def add_char(self, character):
        """
        Add a character to an account's list of registered characters, by name,
        UID, or reference. Raises a ValueError if the character in question has
        not yet been saved.
        """
        pass

    @property
    def characters(self):
        """
        A :class:`frozenset` of names of the characters registered to this
        account. Immutable.
        """
        return utils.CallableFrozenSet(self._characters or [])

