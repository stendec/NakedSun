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
This module provides a simple, flexible hooks system for the MUD.
"""

###############################################################################
# Imports
###############################################################################

import inspect

from . import logger as log

###############################################################################
# Storage and Constants
###############################################################################

_hook_table = {}
_hook_priorities = {}

__all__ = ['hook', 'add', 'remove', 'run', 'build_info', 'parse_info']

###############################################################################
# The Decorators
###############################################################################

def hook(*args, **kwargs):
    """
    This function serves as a decorator for hook functions, allowing for more
    streamlined code than if you were to use :func:`hooks.add`. By default, it
    registers your function for hooks of the function's name. Example::

        @hooks.hook
        def receive_connection(sock):
            pass

    That's equivilent to the following use of :func:`hooks.add`::

        def receive_connection(sock):
            pass

        hooks.add("receive_connection", receive_connection)

    You may provide a string, or list of strings, to register the function with
    different hook(s) than the function's name. Example::

        @hooks.hook("receive_connection", "something_else")
        def my_hook_func(sock):
            pass

    That is, of course, equivilent to::

        def my_hook_func(sock):
            pass

        hooks.add("receive_connection", my_hook_func)
        hooks.add("something_else", my_hook_func)

    You may also provide the ``priority`` and ``old_style`` keyword arguments
    as mentioned in the documentation for :func:`hooks.add`.
    """

    priority = kwargs.get("priority", 0)
    old_style = kwargs.get("old_style", None)

    def outer_hook(*args):
        if callable(args[0]):
            func = args[0]
            add(func.func_name, func, old_style=old_style, priority=priority)
            return func

        def hooker(func):
            for arg in args:
                if not isinstance(arg, basestring):
                    raise TypeError("hooks.hook arguments must be strings.")
                add(arg, func, old_style=old_style, priority=priority)
            return func

        return hooker

    if not args:
        return outer_hook
    return outer_hook(*args)

def add(hook, function, old_style=None, priority=0):
    """
    Register a new function with a hook. Hook functions can accept any number
    of arguments, depending on the specifics of the hook, or maintain
    compatibility with NakedMud by accepting only one arguments, which is then
    processed by :func:`hooks.parse_info` to return a tuple of arguments.

    It is recommended, for performance and ease of use, that all new code avoids
    the use of :func:`hooks.parse_info` unless it's expected to be executed
    within NakedMud as well.

    Functions that make use of :func:`hooks.parse_info`, known as old-style
    hook functions, are incompatible with keyword arguments and will not receive
    them. Old-style functions are automatically detected with the ``inspect``
    module where possible. However, in some cases, a function will not be
    detected properly.

    In that case, setting ``old_style`` to True or False will make the hook
    function behave appropriately.

    ==========  =========  ============
    Argument    Default    Description
    ==========  =========  ============
    hook                   The name of the hook to add the provided function to.
    function               The function to register.
    old_style   ``None``   Whether a particular hook function uses the old-style :func:`hooks.parse_info` or not. A value of ``None`` causes this to be guessed automatically.
    priority    ``0``      The priority of the hook functions. Functions with higher priorities will be executed sooner when a hook is executed.
    ==========  =========  ============
    """
    if old_style is None:
        args = inspect.getargspec(function).args
        old_style = len(args) == 1 and args[0] == 'info'

    if old_style:
        # We've got an old-style function, so wrap it up.
        hooked_for = function
        def function(*args, **kwargs):
            return hooked_for(args)
        function.hooked_for = hooked_for
        function.func_name = hooked_for.func_name

    if not hook in _hook_priorities:
        _hook_priorities[hook] = {}

    if not priority in _hook_priorities[hook]:
        _hook_priorities[hook][priority] = []

    _hook_priorities[hook][priority].append(function)
    rebuild_hook_table(hook)

def rebuild_hook_table(hook):
    """
    Rebuild the table for the given hook, sorting functions based on
    their priorities.
    """
    _hook_table[hook] = []
    if not hook in _hook_priorities:
        del _hook_table[hook]
        return

    for priority in sorted(_hook_priorities[hook].keys(), reverse=True):
        _hook_table[hook].extend(_hook_priorities[hook][priority])

def remove(hook, function):
    """
    Unregister a function from the given hook. This finds the first instance of
    the given function in the hooks table and removes it. This function will
    return True if a function has been removed, or False if the function was
    not registered.

    =========  ============
    Argument   Description
    =========  ============
    hook       The name of the hook to remove the function from.
    function   The function to unregister.
    =========  ============
    """
    if not hook in _hook_priorities:
        return False

    for function_list in _hook_priorities[hook].itervalues():
        for fn in function_list[:]:
            if fn is function or getattr(fn, 'hooked_for', None) is function:
                function_list.remove(fn)
                rebuild_hook_table(hook)
                return True

    return False

def run(hook, *args, **kwargs):
    """
    Execute all of the functions registered with the given hook. This function
    accepts any number of positional and keyword arguments and passes them to
    the registered functions.

    Hook functions are executed in order of their priority, but not otherwise
    sorted. Additionally, a hook function may raise a :class:`StopIteration`
    exception to prevent the remaining functions from running.

    For compatibiltiy with NakedMud, this function supports the use of
    :func:`hooks.build_info`. The following example demonstrates both the old
    and new ways of running a hook::

        # Old Method
        hooks.run("receive_connection", hooks.build_info("sk", (sock, )))

        # New Method
        hooks.run("receive_connection", sock)

    =========  ============
    Argument   Description
    =========  ============
    hook       The name of the hook to run.
    =========  ============
    """
    if not hook in _hook_table:
        return

    if args and isinstance(args[0], BuildInfoTuple):
        if len(args) > 1 or kwargs:
            raise ValueError(
                "Please only provide a single argument to hooks.run when "
                "using hooks.build_info to avoid confusion.")
        args = args[0]

    for function in _hook_table[hook]:
        try:
            function(*args, **kwargs)
        except StopIteration:
            break
        except SystemExit:
            raise
        except Exception:
            log.exception("An error occurred while running a function for "
                          "the hook %r." % hook)

###############################################################################
# build_info and parse_info
###############################################################################

class BuildInfoTuple(tuple):
    """
    This subclass of tuple is used internally by NakedSun to keep track of the
    usage of hooks.build_info.
    """
    pass

def build_info(format, args):
    """
    This function exists only for compatibility with legacy NakedMud code and
    should only be used if you're writing code that must work within NakedMud
    as well as NakedSun.

    Please see the
    `NakedMud documentation <http://nakedmud.org/media/pydocs/hooks.html>_` for
    more information.

    =========  ============
    Argument   Description
    =========  ============
    format     A space-separated string of variable types.
    args       A tuple of variables to pack into an information object.
    =========  ============
    """
    return BuildInfoTuple(args)

def parse_info(info):
    """
    This function exists only for compatibility with legacy NakedMud code and
    should only be used if you're writing code that must work within NakedMud
    as well as NakedSun.

    Please see the
    `NakedMud documentation <http://nakedmud.org/media/pydocs/hooks.html>_` for
    more information.

    =========  ============
    Argument   Description
    =========  ============
    info       An information object to unpack into a tuple.
    =========  ============
    """
    return info
