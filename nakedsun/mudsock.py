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
import codecs

import pants.util.dns
from time import time as now
import weakref

from . import auxiliary
from . import hooks
from . import logger as log
from . import settings

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
        connection.read_delimiter = "\n"
        connection.on_read = self._on_read

        # Internal State
        self._out_buffer = []
        self._ihs = []
        self._ch = None
        self._encoding = None
        self._account = None
        self._can_use = False
        self._hostname = None
        self._last_activity = now()

        # Set the default text encoding.
        self.set_encoding(settings.get("default_encoding", "utf8"))

        # Weird public variable.
        self.outbound_text = None

        # Store a reference to this instance.
        self._ref = weakref.ref(self)
        _sockets.append(self._ref)

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

    ##### Encoding #############################################################

    def set_encoding(self, encoding):
        """
        Set the socket's character encoding to the provided encoding, allowing
        the transfer of unicode across the connection. If necessary, an
        incremental decoder is created for reading the received data.
        """
        if encoding == self._encoding:
            return
        self._encoding = encoding

        # Get an incremental decoder.
        try:
            self._decoder = codecs.getincrementaldecoder(encoding)("replace")
        except LookupError:
            self._decoder = None

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
                              "connection #%d." % (state, self._uid))

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
        This is a convenience function that first pops the current input
        handler from the stack before pushing the new input handler.
        """
        self.pop_ih()
        self.push_ih(handler_func, prompt_func, state, cleanup_func)

    ##### Communication Internals #############################################

    def _handle_write(self, mode="text"):
        """
        Iterate through the output buffer and call the appropriate hooks.
        """
        output = []
        self.outbound_text = []

        while self._out_buffer:
            out = self._out_buffer.pop(0)

            # If we run across an actual string and not a unicode string, flush
            # everything out so we can send that raw.
            if isinstance(out, str):
                if self.outbound_text:
                    self.outbound_text = u"".join(self.outbound_text)
                    hooks.run("process_outbound_%s" % mode, self)
                    hooks.run("finalize_outbound_%s" % mode, self)
                    output.append(self.outbound_text.encode(self._encoding,
                        "replace").replace("\xFF", "\xFF\xFF"))
                    self.outbound_text = []
                output.append(out)
            else:
                self.outbound_text.append(out)

        # Now, flush outbound_text.
        if self.outbound_text:
            self.outbound_text = u"".join(self.outbound_text)
            hooks.run("process_outbound_%s" % mode, self)
            hooks.run("finalize_outbound_%s" % mode, self)
            output.append(self.outbound_text.encode(self._encoding,
                "replace").replace("\xFF", "\xFF\xFF"))

        # Clear outbound_text and send output.
        self.outbound_text = None
        for out in output:
            self._connection.write(out)

    def _perform_write(self):
        """
        Process the output buffer and send it on to the networking layer.
        """
        self._scheduled_for_write = False

        # If there's no connection, clearly we can't send anything. We'll be
        # cleaned up soon too, so just return for now.
        if not self._connection or not self._connection.connected:
            return

        # Run a useless hook!
        hooks.run("flush", self)

        # If we don't have anything to write out, just end now.
        if not self._out_buffer and (not self._ihs or not self._busted):
            return

        # Handle the output buffer.
        self._handle_write()

        # Now, the prompt.
        if self._busted:
            self._show_prompt()
            self._handle_write("prompt")

        # Clear outbound text now that we're all done.
        self.outbound_text = None

    _scheduled_for_write = False

    def _schedule_write(self):
        """
        Schedule this connection to have data sent to the remote client on the
        next pulse.
        """
        if not self._scheduled_for_write:
            self._scheduled_for_write = True
            pants.engine.callback(self._perform_write)

    def _show_prompt(self):
        """
        Display the prompt.
        """
        self._busted = False
        if not self._ihs:
            return

        try:
            self._ihs[-1][1](self)
        except Exception:
            state = self._ihs[-1][2]
            log.exception("An error occurred while running the prompt display "
                          "function for state %r on connection #%d." %
                          (self._ihs[-1][2], self._uid))

    ##### Communication #######################################################

    _busted = False

    def bust_prompt(self):
        """
        Mark the connection to have its prompt re-sent next pulse.
        """
        self._busted = True
        self._schedule_write()

    def close(self):
        """ Close the connection. """

        # Reference cleanup.
        if self._ref in _sockets:
            _sockets.remove(self._ref)

        # Character cleanup.
        if self._ch:
            log.todo("Disassociate character from closing socket.")

        # Account cleanup. Yay.
        if self._account:
            self._account = None

        # Handler cleanup.
        while self.pop_ih():
            continue

        # Socket cleanup.
        if self._connection:
            con = self._connection
            self._connection = None
            con.close()

        # Ex-ter-min-ate.

    def send(self, message, environ=None, newline=True):
        """
        Send the message to the remote host. Additionally, if an environment is
        provided, the message will be processed with the active template engine
        before being sent. If newline is True, a line return will be appended
        to the message as well.

        .. note::

            NakedSun uses unicode internally, so any byte strings passed to
            this function will be converted into unicode before they're sent to
            the remote client.

            If you need to send raw bytes, such as for sending telnet
            sequences, you should use :func:`send_data`.
        """
        if not isinstance(message, unicode):
            message = message.decode(self._encoding)

        if environ:
            log.todo("Implement a template engine.")

        if newline:
            message += "\r\n"

        self._out_buffer.append(message)
        self._schedule_write()

    def send_raw(self, message):
        """
        Send the message to the remote host without appending a line return.

        .. note::

            NakedSun uses unicode internally, so any byte strings passed to
            this function will be converted into unicode before they're sent to
            the remote client.

            If you need to send raw bytes, such as for sending telnet
            sequences, you should use :func:`send_data`.
        """
        self.send(message, newline=False)

    def send_data(self, data):
        """
        Send a raw string to the remote client. This string will not be
        processed with any hooks prior to being sent.
        """
        if not isinstance(data, str):
            raise TypeError("Only byte strings may be sent with send_data.")
        self._out_buffer.append(data)
        self._schedule_write()

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

    def _on_read(self, data):
        """
        Handle incoming text from the remote host. Convert it into unicode and
        pass it along to the input handler.
        """
        if data.endswith("\r"):
            data = data[:-1]

        # Make sure we have an input handler. If not, give the socket one chance
        # to acquire one.
        if not self._ihs:
            hooks.run("bare_socket", self)
            if not self._ihs and self._connection.connected:
                log.warning("Closing connection #%d as it lacks input "
                            "handlers." % self._uid)
                self.close()
                return

        # Send the data through the input handlers.
        handlers = self._ihs[:]
        while data:
            handler, prompt, state = handlers.pop()[:3]
            try:
                data = handler(self, data)
            except Exception:
                log.exception("An error occurred while running the input "
                              "handler for state %r on connection #%d." %
                              (state, self._uid))
                break

        # Bust the prompt.
        self.bust_prompt()

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
