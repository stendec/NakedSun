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

import nakedsun.logger as log

###############################################################################
# Storage and Constants
###############################################################################

_hook_table = {}
_hook_priorities = {}

# Unique object for build_info and parse_info tricks.
_BuildInfoThing = object()

###############################################################################
# The Decorators
###############################################################################

def hook(*a,**kw):
    """
    This function serves as a decorator for hook functions, allowing for more
    streamlined code than if you were to use :func:`hooks.add`.
    
    By default, it registers your function for hooks of the function name.
    Example::
        
        @hooks.hook
        def receive_connection(sock):
            pass
    
    That's equivilent to::
        
        def receive_connection(sock):
            pass
        
        hooks.add("receive_connection", receive_connection)
    
    If you provide a string, or multiple strings, the function will instead be
    registered for those hooks. Example::
        
        @hooks.hook("receive_connection", "something_else")
        def my_hook_func(sock):
            pass
    
    That's equivilent to::
        
        def my_hook_func(sock):
            pass
        
        hooks.add("receive_connection", my_hook_func)
        hooks.add("something_else", my_hook_func)
    
    You may also specify a ``priority`` and ``old_style`` flag, as mentioned
    in the documentation for :func:``hooks.add``.
    """

    priority = kw.get('priority',0)
    old_style = kw.get('old_style', None)

    def outer_hook(*args):
        if callable(args[0]):
            add(args[0].func_name, args[0], old_style=old_style, priority=priority)
            return args[0]

        def hooker(func):
            for arg in args:
                if not isinstance(arg, basestring):
                    continue
                add(arg, func, old_style=old_style, priority=priority)
            return func
        
        return hooker
    
    if not a:
        return outer_hook
    return outer_hook(*a)

def add(hook, function, old_style=None, priority=0):
    """
    Register a new function with a hook. Hook functions can accept any number
    of arguments, depending on the specifics of the hook, or maintain
    compatibility with NakedMud by accepting only one argument, which is then
    processed by :func:`hooks.parse_info` to return a tuple of arguments.
    
    It is recommended, for performance, that all new code avoids the use of
    :func:`hooks.parse_info` except where it may also be used with NakedMud,
    for performance reasons.
    
    Old-style functions are incompatible with keyword arguments, and will not
    receive them. Generally, old-style functions will be automatically detected
    via the ``inspect`` module. If this doesn't work properly, you can set
    ``old_style`` to True or False to override the automatic detection.
    
    ==========  ============
    Argument    Description
    ==========  ============
    hook        The string key of the hook to add a function for.
    function    The function to add.
    old_style   *Optional.* If this is set, it will override automatic detection of whether or not the function is an old-style NakedMud compatible hook function.
    priority    *Optional.* The priority for this function. By default, this is ``0``.
    ==========  ============
    """
    
    if old_style is None:
        args = inspect.getargspec(function).args
        old_style = len(args) == 1 and args[0] == 'info'
    
    if old_style:
        hooked_for = function
        def old_wrapper(*args,**kwarg):
            hooked_for(args)
        old_wrapper.__hooked_for = hooked_for
        old_wrapper.func_name = hooked_for.func_name
        function = old_wrapper
    
    if not hook in _hook_priorities:
        _hook_priorities[hook] = {}
    
    if not priority in _hook_priorities[hook]:
        _hook_priorities[hook][priority] = []
    
    _hook_priorities[hook][priority].append(function)
    __rebuild_hooktable(hook)

def __rebuild_hooktable(hook):
    """ Rebuild part of the hooktable, resorting functions based on their
        priorities.
    """
    _hook_table[hook] = []
    if not hook in _hook_priorities:
        del _hook_table[hook]
        return
    
    priorities = sorted(_hook_priorities[hook].keys(), reverse=True)
    for p in priorities:
        _hook_table[hook].extend(_hook_priorities[hook][p])

def build_info(format, args):
    """
    This function exists only for compatibility with NakedMud, and should only
    be used if you're writing code that must work within NakedMud as well as
    NakedSun.
    
    Please see the NakedMud documentation for more information.
    
    =========  ============
    Argument   Description
    =========  ============
    format     A space-separated string of variable types.
    args       A tuple of variables to encode into an information variable.
    =========  ============
    """
    if not isinstance(args, (list,tuple)):
        raise ValueError("args must be a tuple or list.")
    
    return (_BuildInfoThing,) + args

def parse_info(info):
    """
    This function exists only for compatibility with NakedMud, and should only
    be used if you're writing code that must work within NakedMud as well as
    NakedSun.
    
    Please see the NakedMud documentation for more information.
    
    =========  ============
    Argument   Description
    =========  ============
    info       An information variable to decode into a tuple.
    =========  ============
    """
    if info and info[0] is _BuildInfoThing:
        info = info[1:]
    
    return info

def remove(hook, function):
    """
    Unregister a hook function. This finds the first instance of the given
    function in the hooks table for the given hook and removes it. It finds
    both old-style and new-style functions.
    
    This function will return True if a function has been removed, or False if
    the function was not there to be removed.
    
    ===========  ============
    Argument     Description
    ===========  ============
    hook         The string key of the hook to remove a function from.
    function     The function to remove.
    ===========  ============
    """
    if not hook in _hook_priorities:
        return False
    
    for fs in _hook_priorities[hook].itervalues():
        for func in fs[:]:
            if func is function or (hasattr(func, '__hooked_for') and \
                    func.__hooked_for is function):
                fs.remove(func)
                __rebuild_hooktable(hook)
                return True
    
    return False

def run(hook, *args, **kwargs):
    """
    Run all the functions registered with a given hook. This function accepts
    any arguments and keyword arguments, passing them along to the functions.
    
    In addition, for compatibility with NakedMud, this function accepts the
    output of :func:`hooks.build_info`.
    
    =========  ============
    Argument   Description
    =========  ============
    hook       The string key of the hook to run.
    =========  ============
    """
    if not hook in _hook_table:
        return
    
    if args and isinstance(args[0],tuple) and len(args[0]) >= 1 and \
            args[0][0] is _BuildInfoThing:
        if len(args) > 1 or kwargs:
            raise ValueError("Please only provide a single argument when " + \
                "using hooks.build_info to avoid confusion.")
        args = args[0][1:]
    
    for func in _hook_table[hook]:
        try:
            func(*args, **kwargs)
        except StopIteration:
            break
        except SystemExit:
            raise
        except Exception:
            log.exception(u'Error running function for hook: %s' % hook)
