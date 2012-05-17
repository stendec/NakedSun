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
This module is the core of the network connectivity of NakedSun, creating the
actual servers and handling new connections.
"""

###############################################################################
# Imports
###############################################################################

from pants.contrib.telnet import TelnetConnection
from pants import Server

from . import hooks
from . import logger as log
from . import mudsock
from . import settings

###############################################################################
# Storage and Constants
###############################################################################

main_server = None
http_server = None

###############################################################################
# Simple Connections
###############################################################################

class SimpleTelnet(TelnetConnection):
    """
    This class is used with raw telnet connections.
    """

    ms = None

    def on_connect(self):
        self.ms = mudsock.Mudsock(self)
        hooks.run("receive_connection", self.ms)
        self.ms.bust_prompt()

    def on_close(self):
        if self.ms:
            self.ms.close()

###############################################################################
# Initialization
###############################################################################

def _parse_address(addr):
    """
    Parse an address, keeping aware of IPv6.
    """
    addr = addr.strip()
    if addr.startswith('[') and ']' in addr:
        host, _, port = addr[1:].partition(']')
        if not port.startswith(':'):
            raise ValueError("Invalid address.")
        port = int(port[1:])
    else:
        host, _, port = addr.partition(':')
        port = int(port)

    return host, port

def initialize(addr, http_addr):
    """
    Initialize the servers and start listening.
    """
    global main_server
    global http_server

    if not addr:
        addr = settings.get("main_addr", ":4000")

    if not http_addr:
        http_addr = settings.get("http_addr", ":8080")

    # Parse the addresses.
    addr = _parse_address(addr)
    http_addr = _parse_address(http_addr)

    # Create the main server.
    main_server = Server(SimpleTelnet)
    main_server.listen(addr)

    log.todo("Initialize the HTTP server.")

def stop_listeners():
    """
    Shut down the listening servers. Existing connections will remain active.
    """
    global main_server
    global http_server

    if main_server:
        main_server.close()
        main_server = None

    if http_server:
        http_server.close()
        http_server = None
