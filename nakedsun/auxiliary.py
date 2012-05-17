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
This module provides the auxiliary data systems, a function for registering new
auxiliary data classes, and a base class that all classes supporting auxiliary
data inherit.
"""

###############################################################################
# Imports
###############################################################################

import weakref

from . import logger as log

###############################################################################
# Storage and Constants and Stupid Classes
###############################################################################

_classes = {}
_types = {}

class _EmptyOldStyle:
    pass

###############################################################################
# Public Functions
###############################################################################

def install(name, cls, installs_on):
    """
    Register a new auxiliary data class to the given name on the given classes.
    Auxiliary data can be installed on: character, object, room, account,
    socket, and exit.

    An auxiliary data class must provide the following functions:

        class ExampleClass(object):
            def __init__(self, storage_set=None):
                '''
                Initialize the auxiliary data storage instance, using data from
                the provided storage.StorageSet instance.
                '''
                ...

            def copy(self):
                '''
                Create a copy of the auxiliary data storage instance and return
                it. In many cases, return self.copyTo(self.__class__()) should
                prove sufficient.
                '''
                ...

            def copyTo(self, to):
                '''
                Copy the data from this auxiliary data storage instance to
                another instance.
                '''
                ...

            def store(self):
                '''
                Return a storage.StorageSet or Python dictionary containing the
                entirety of the data contained in this auxiliary data storage
                instance. If there is no data, returning an empty StorageSet or
                simply None will suffice.

                If your code needs to remain compatible with NakedMud, please
                refrain from returning anything but a storage.StorageSet.
                '''
                ...

    In NakedSun, auxiliary data storage classes all contain a reference to the
    object they're associated with. Whether the auxiliary data is attached to
    an account, character, or any class, simply use ``self.owner`` to access
    the instance.

    .. note::

        The ``self.owner`` attribute will not be made available to any class
        using ``__slots__`` unless owner is defined in the list of slots.
    """

    # First, run a sanity check on the new class.
    if not hasattr(cls, "copy") or not hasattr(cls, "copyTo") or \
            not hasattr(cls, "store"):
        raise TypeError("The class %r does not contain all of the functions "
                        "required to act as an auxiliary data storage class.")

    if not isinstance(name, basestring):
        raise TypeError("The auxiliary data name must be a string.")

    # Store the class in our table.
    for word in installs_on.split(","):
        # Strip the word and convert it to lower case. Also make sure the word
        # in question has a table entry.
        word = word.strip().lower()
        if not word in _classes:
            _classes[word] = {}

        # If we're overwriting an existing class, log a warning.
        if name in _classes[word]:
            old = _classes[word][name]
            log.warning("Overwriting existing auxiliary data class %r on type "
                        "%r %s with %s." % (name, word, repr(old), repr(cls)))

        # Set it and move on.
        _classes[word][name] = cls

def register(name, cls=None):
    """
    This class decorator registers a new class with auxiliary data support to a
    given name, allowing that name to be used in the ``installs_on`` argument
    of :func:`install`.
    """

    def decorator(cls):
        _types[cls] = name.strip().lower()
        return cls

    if cls:
        return decorator(cls)
    return decorator

###############################################################################
# Not As Public Functions
###############################################################################

def _determine_class(thing):
    """
    Iterate through the registered classes with auxiliary data support.
    """
    for key, val in _types.iteritems():
        if isinstance(thing, key):
            return val
    return None

def _get_class(owner, cls):
    """
    Get the auxiliary data storage class with the name ``cls``.
    """

    # Get the type of owner.
    owner_type = _determine_class(owner)
    if not owner_type:
        raise TypeError("Cannot initialize auxiliary data on unregistered "
                        "type %r." % type(owner))

    if not cls in _classes[owner_type]:
        raise KeyError("No such auxiliary data class %r for type %r." %
                       (cls, owner_type))

    # Store the class.
    return _classes[owner_type]

def _initialize(owner, cls, data=None, key=None):
    """
    Initialize an instance of an auxiliary data storage class on the provided
    object with the name ``cls``, using the provided :class:`storage.StorageSet`
    instance if there's existing data.

    Additionally, if you already have the auxiliary data storage class, you may
    pass the class directly.
    """

    # Make sure the class is a class.
    if isinstance(cls, basestring):
        key = cls
        cls = _get_class(owner, cls)

    # Now, we have an owner and a class. Let's create an instance of the class.

    if isinstance(cls, type):
        # New style classes are awesome.
        instance = cls.__new__(cls, data)

    else:
        # Old style classes are not.
        instance = _EmptyOldStyle()
        instance.__class__ = cls

    # Now, set the owner reference and call the __init__ function.
    instance.owner = weakref.proxy(owner)
    instance.__init__(data)

    # Store it in the owner's auxiliary table.
    if key:
        if not owner._auxiliary:
            owner._auxiliary = {}

        owner._auxiliary[key] = instance

    # And finally return it.
    return instance

###############################################################################
# The Almighty Base Class
###############################################################################

class AuxiliaryBase(object):
    """
    This class is meant to be inherited by any classes with support for
    auxiliary data, and is inherited by :class:`account.Account`,
    :class:`char.Char`, :class:`exit.Exit`, :class:`mudsock.Mudsock`,
    :class:`obj.Obj`, and :class:`room.Room`.
    """

    # Set this variable to prevent AttributeErrors later.
    _auxiliary = None

    ##### Private Functions ####################################################

    def _auxiliary_init(self, data=None):
        """
        Initialize all the auxiliary data storage classes associated with this.
        """
        my_type = _determine_class(self)
        if not my_type:
            return

        # Iterate through the classes.
        for key, cls in _classes[my_type].iteritems():
            key_data = data[key] if data and key in data else None

            try:
                _initialize(self, cls, key_data, key)
            except Exception:
                log.exception("There was an error initializing the auxiliary "
                              "data storage class %r for %r." % (key, self))

    ##### Public Functions #####################################################

    def aux(self, name):
        """
        Return the auxiliary data storage class instance for this with the
        given name. A KeyError is raised if the provided name isn't a registered
        auxiliary data name.

        Returns None if there was a problem initializing the auxiliary data
        storage class, or if the auxiliary data name wasn't registered at the
        time this was initialized.
        """
        if not self._auxiliary or not name in self._auxiliary:
            # Check that it's a valid name.
            _get_class(self, name)
            return None

        return self._auxiliary[name]

    getAuxiliary = aux

