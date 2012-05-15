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
This module provides simple timers for NakedSun, built on top of the timers and
callbacks available in the Pants networking library. This is mostly for
compatibility with NakedMud.
"""

###############################################################################
# Imports
###############################################################################

import weakref

from pants.engine import Engine

###############################################################################
# Storage
###############################################################################

__queued__ = {}

###############################################################################
# Functions
###############################################################################

def interrupt_events_involving(thing):
    """
    De-schedule any currently pending events involving the provided object.
    """
    if not thing in __queued__:
        return

    for t in __queued__[thing]:
        try:
            t()
        except weakref.ReferenceError:
            pass
    del __queued__[thing]

def start_event(owner, delay, event_func, data=None, arg='', *args, **kwargs):
    """
    Schedule a new event to trigger after ``delay`` seconds. Owners may be any
    Python object, but should be an instance of one of:
    :class:`account.Account`, :class:`char.Char`, :class:`exit.Exit`,
    :class:`mudsock.Mudsock`, :class:`obj.Obj`, or :class:`room.Room`.

    If the owner *is* one of those classes, any currently pending events are
    de-scheduled automatically when the owner is destroyed.

    Event functions should take a minimum of three arguments: the event owner,
    ``data``, and ``arg``. This is for compatibility with NakedMud. You may
    provide additional positional and keyword arguments if you wish.

    Returns a callable that de-schedules the event when called.

    ===========  ============
    Argument     Description
    ===========  ============
    owner        The object that owns the event.
    delay        How long, in seconds, to wait before the event function should be called.
    event_func   The function to be called.
    data         *Optional.* Any Python object to be provided to the event function.
    arg          *Optional.* A string to be provided to the event function.
    ===========  ============
    """
    if not owner in __queued__:
        __queued__[owner] = []

    event = Engine.instance().defer(delay, event_func, owner, data, arg, *args, **kwargs)
    __queued__[owner].append(event)
    return event

def next_pulse(function, *args, **kwargs):
    """
    Run the provided function on the next pulse.
    """
    Engine.instance().callback(function, *args, **kwargs)
