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
This module contains the Mudsock class, which represents connections to the MUD
server and deals with telnet state.
"""

###############################################################################
# Imports
###############################################################################

import pants
from time import time as now
import weakref

from . import auxiliary
from . import hooks
from . import logger as log

###############################################################################
# Storage and Constants
###############################################################################

_sockets = []

###############################################################################
# Mudsock Class
###############################################################################

@auxiliary.register("socket")
class Mudsock(auxiliary.AuxiliaryBase):
    """
    The Mudsock class is in some ways the most important part of NakedSun, as
    it provides for communication with the connecting players. Mudsock supports
    unicode when clients negotiate it, and has a full telnet state machine
    built-in.

    Auxiliary data may be attached to sockets, however it is not saved for
    obvious reasons.

    Data received by a connection is processed via the list of input handlers
    associated with the Mudsock with :func:`push_ih` and :func:`pop_ih`. See
    those functions for more information.
    """

    _last_uid = 0

    def __init__(self, connection):
        """
        Initialize the default state and connect to the provided connection.
        The connection is expected to be an instance of
        :class:`pants.contrib.telnet.TelnetConnection` or a class with a
        compatible API.
        """

        # Set the unique ID for this connection.
        Mudsock._last_uid += 1
        self._uid = Mudsock._last_uid

        # Connect to the connection.
        self._connection = connection

        # Internal State
        self._ihs = []
        self._ch = None
        self._account = None
        self._can_use = False
        self._hostname = None
        self._last_activity = now()

        # Weird public variable.
        self.outbound_text = None

        # Store a reference to this instance.
        _sockets.append(weakref.ref(self))

        # Start resolving the hostname.

        pants.util.dns.gethostbyaddr(connection.remote_addr[0], self._got_host)

    ##### Properties ###########################################################

    @property
    def account(self):
        """
        The :class:`account.Account` currently associated with the connection.
        Immutable. Returns None if there is no associated account. See
        :func:`mudsys.attach_account_socket` to associate an account with a
        connection.
        """
        return self._account

    @property
    def can_use(self):
        """
        Effectively, whether or not the remote host's address has been looked
        up yet. This property exists for compatibility with NakedMud, and can
        be replaced with the ``dns_complete`` hook.
        """
        return self._can_use

    @property
    def character(self):
        """
        The :class:`char.Char` currently associated with the connection.
        Immutable. Returns None if there is no associated character. See
        :func:`mudsys.attach_char_socket` to associate a character with a
        connection.
        """
        return self._ch

    ch = char = character

    @property
    def hostname(self):
        """ The hostname of the remote machine. """
        return self._hostname or self._connection.remote_addr[0]

    @property
    def idle_time(self):
        """
        How long, in seconds, since there was activity on the connection.
        """
        return now() - self._last_activity

    @property
    def state(self):
        """
        The state of the connection. Immutable. For more on states, see
        :func:`mudsock.Mudsock.push_ih`. Returns an empty string if there aren't
        currently any input handlers.
        """
        return self._ihs[-1][-1][2] if self._ihs else ""

    @property
    def uid(self):
        """ The unique ID for this connection. """
        return self._uid

    ##### Input Handlers #######################################################

    def pop_ih(self):
        """
        Pop the connection's current input handler from the stack, and returns
        True if an input handler was removed or False if the stack was already
        empty. You can completely clear the input handler stack with::

            while sock.pop_ih():
                continue

        If the removed input handler has a cleanup function, that function will
        be called by this function.
        """
        if not self._ihs:
            return False

        # Pop it off.
        handler, prompt, state, cleanup = self._ihs.pop()

        # And call the cleanup function.
        if cleanup:
            try:
                cleanup(self)
            except Exception:
                if not state:
                    state = handler.func_name
                log.exception("An error occurred while running the input "
                              "handler cleanup function for the state %r on "
                              "%r." % (state, self))

        return True

    def push_ih(self, handler_func, prompt_func=None, state=None,
                cleanup_func=None):
        """
        Push a new input handler onto the stack.
        """
        if not callable(handler_func):
            raise TypeError("The handler function must be callable.")

        if not prompt_func:
            if not self._ihs:
                raise TypeError("The prompt function must be callable.")
            prompt_func = self._ihs[-1][1]

        if state is None:
            state = self._ihs[-1][2] if self._ihs else ""

        # Append this input handler.
        self._ihs.append((handler_func, prompt_func, state, cleanup_func))

    def replace_ih(self, handler_func, prompt_func=None, state=None,
                   cleanup_func=None):
        """
        This is a convenience function that first pops the current input handler
        from the stack before pushing the new input handler.
        """
        self.pop_ih()
        self.push_ih(handler_func, prompt_func, state, cleanup_func)

    ##### Private Event Handlers ###############################################

    def _got_host(self, result):
        """
        This is the callback method called when reverse resolution of the IP
        address has completed.
        """
        if result:
            self._hostname = result[0]

        # Now, notify other code that we're done.
        self._can_use = True
        hooks.run("dns_complete", self)

###############################################################################
# Public Functions
###############################################################################

def socket_gen():
    """ Returns a generator that will iterate through all Mudsock instances. """
    for ref in _sockets[:]:
        sock = ref()
        if not sock:
            _sockets.remove(ref)
            continue
        yield sock

def socket_list():
    """ Returns a list of all Mudsock instances. """
    return list(socket_gen())
