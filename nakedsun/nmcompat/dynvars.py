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
Dynamic Variables for Characters, Rooms, and Objects.
"""

###############################################################################
# Imports
###############################################################################

from nakedsun import auxiliary
from nakedsun import mudsys
from nakedsun import storage

###############################################################################
# Constants
###############################################################################

AUX_KEY = "dyn_var_aux_data"

###############################################################################
# DynVarAux Class
###############################################################################

class DynVarAux(object):
    __slots__ = ('data',)

    def __init__(self, set=None):
        self.data = {}
        if set:
            for key in set:
                self.data[key] = set[key]

    def copyTo(self, to):
        to.data = self.data.copy()
        return to

    def copy(self):
        return self.copyTo(DynVarAux())

    def store(self):
        set = storage.StorageSet()
        for key in self.data:
            set[key] = self.data[key]
        return set

###############################################################################
# Helper Functions
###############################################################################

def getter(thing, key):
    """
    Returns the value of a variable attached to the character, room, or object
    in question, or if a value has not been set, returns 0.
    """
    return thing.aux(AUX_KEY).data.get(key, 0)

def setter(thing, key, val):
    """
    Set the value of a variable attached to the character, room, or object in
    question. Values must be boolean, numbers, or strings.

    This is provided for compatibility with NakedMud, and is generally not the
    best way to attach custom information to something.
    """
    if not type(val) in (str,unicode,int,long,float,bool):
        raise TypeError("Invalid data type.")
    thing.aux(AUX_KEY).data[key] = val

def deleter(thing, key):
    """
    Delete a variable that's attached to the character, room, or object in
    question, if they have one by the given name. If a variable does not exist,
    this does nothing.
    """
    try:
        del thing.aux(AUX_KEY).data[key]
    except KeyError:
        pass

def has(thing, key):
    """
    Returns True if the character, room, or object in question has a variable
    attached to it with the given key.
    """
    return key in thing.aux(AUX_KEY).data

###############################################################################
# Initialization
###############################################################################

auxiliary.install(AUX_KEY, DynVarAux, "character, room, object")

mudsys.add_char_method("deletevar", deleter)
mudsys.add_char_method("delvar", deleter)
mudsys.add_char_method("getvar", getter)
mudsys.add_char_method("hasvar", has)
mudsys.add_char_method("setvar", setter)

mudsys.add_room_method("deletevar", deleter)
mudsys.add_room_method("delvar", deleter)
mudsys.add_room_method("getvar", getter)
mudsys.add_room_method("hasvar", has)
mudsys.add_room_method("setvar", setter)

mudsys.add_obj_method("deletevar", deleter)
mudsys.add_obj_method("delvar", deleter)
mudsys.add_obj_method("getvar", getter)
mudsys.add_obj_method("hasvar", has)
mudsys.add_obj_method("setvar", setter)
