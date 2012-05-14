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
This module provides simple bitvectors for the MUD.
"""

###############################################################################
# Storage and Constants
###############################################################################

bitvectors = {}

__all__ = ['Bitvector', 'create_bitvector']

_setattr = object.__setattr__

###############################################################################
# Helper Functions
###############################################################################

def _bits_from_string(vector, words):
    if isinstance(vector, basestring):
        vector = bitvectors[vector]
    
    out = set()
    
    for word in words.split(','):
        word = word.strip()
        if word in vector:
            out.add(word)
        else:
            raise ValueError("No such bit, %s" % word)
    
    return out

###############################################################################
# Bitvector Class
###############################################################################

class Bitvector(object):
    __slots__ = ('_vecname', '_vector', '_bits')
    
    def __init__(self, vector, bits=None):
        if isinstance(vector, Bitvector):
            _setattr(self, '_vector', vector._vector)
            _setattr(self, '_vecname', vector._vecname)
            _setattr(self, '_bits', vectors._bits.copy())
        else:
            if not isinstance(vector, basestring):
                raise TypeError("Vector must be a string key.")
            
            _setattr(self, '_vecname', vector)
            
            vector = bitvectors[vector]
            _setattr(self, '_vector', vector)
            
            if not bits:
                _setattr(self, '_bits', set())
            elif isinstance(bits, basestring):
                _setattr(self, '_bits', _bits_from_string(vector, bits))
            else:
                _setattr(self, '_bits', bits)
    
    def __contains__(self, key):
        return key in self._bits
    
    def __getattr__(self, key):
        if key[0] == '_':
            raise AttributeError
        
        if not key in self._vector:
            raise AttributeError
        
        return key in self._bits
    
    def __setattr__(self, key, val):
        val = bool(val)
        if not key in self._vector:
            raise AttributeError
        
        if val:
            self._bits.add(key)
        elif key in self._bits:
            self._bits.remove(key)
    
    def __str__(self):
        return ', '.join(sorted(self._bits))
    
    def __repr__(self):
        return '<Bitvector(%s:%s)>' % (self._vecname, self.__str__())
    
    def any(self):
        return bool(self._bits)
    
    def clear(self):
        _setattr(self, '_bits', set())
    
    def copy(self):
        return self.__class__(self)
    
    def setall(self, val):
        """
        Set all bits to either True or False.
        """
        if val:
            _setattr(self, '_bits', set(self._vector))
        else:
            _setattr(self, '_bits', set())
    
    def __and__(self, b):
        return Bitvector(self._vecname, self._bits & b._bits)
    
    def __or__(self, b):
        return Bitvector(self._vecname, self._bits | b._bits)
    
def create_bitvector(bitvector, *bits):
    """
    Create a new bitvector with the specified bits, or extend a previously
    existing bitvector with new bits.
    
    ==========  ============
    Argument    Description
    ==========  ============
    bitvector   The bitvector to create or modify.
    *bits       The bits to add as any number of strings.
    ==========  ============
    """
    if not bitvector in bitvectors:
        bitvectors[bitvector] = []
    
    if bits:
        bitvectors[bitvector].extend(bits)

###############################################################################
# Default Bitvectors
###############################################################################

create_bitvector('user_groups',
            'player', 'playtester', 'builder', 'scripter', 'wizard', 'admin')
create_bitvector('char_prfs')
create_bitvector('obj_bits', 'notake')
create_bitvector('room_bits')
