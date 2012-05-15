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
A storage engine compatible with NakedMud's odd file format.
"""

###############################################################################
# Basic Settings
###############################################################################
# Unicode is awesome.
ENCODING        = 'utf8'

# Don't mess with this if you want stock-NM compatibility.
INDENT_RATE     = 2
SET_MARKER      = '-'
LIST_MARKER     = '='
STRING_MARKER   = '~'
TYPELESS_MARKER = ' '

# Make sure this is never, ever used in your storagesets. That's why the NULL
# bytes come in handy. NM isn't NULL friendly.
READ_ORDER_KEY  = '\x00\x00READORDER\x00\x00'
LONGEST_KEY     = '\x00\x00LONGEST\x00\x00'

###############################################################################
# Code Stuff
###############################################################################

class PeekFile(object):
    """ This class provides a peekline function for the wrapped file object,
        which is necessary for the storageset reading. """
    
    def __init__(self, file):
        self.file = file
        self.old_line = None
    
    def peekline(self):
        if self.old_line is None:
            self.old_line = self.file.readline()
        return self.old_line
    
    def readline(self):
        if self.old_line is None:
            return self.file.readline()
        val = self.old_line
        self.old_line = None
        return val

class StorageList(object):
    __slots__ = ('parent','modified','_list')

    def __init__(self, list=None, parent=None):
        self.parent = parent
        self.modified = False
        
        if list is None:
            list = []
        self._list = list
    
    def _modified(self):
        self.modified = True
        if self.parent:
            self.parent._modified()
    
    def add(self, set):
        """ Append a new storage set to the storage list. """
        if not isinstance(set, StorageSet):
            raise TypeError("set must be a StorageSet!")
        
        if self.parent is set:
            raise ValueError("Let's not enter an infinite loop today, thanks.")
        
        if set.parent is None:
            set.parent = self
        
        self._list.append(set._data)
        self._modified()
    
    def sets(self):
        """ Returns a Python list of all the sets in the storage list. """
        return list(self)
    
    def __iter__(self):
        return (StorageSet(data=x, parent=self) for x in self._list)

## The StorageSet Class
class StorageSet(object):
    __slots__ = ('parent','modified','_data')

    def __init__(self, filename=None, data=None, parent=None):
        """ Create a new storage set. If a filename is supplied, read a storage
            set in from the specified file.
        """
        
        self.parent = parent
        self.modified = False
        
        if data is None:
            data = {}
        self._data = data
        
        if filename:
            self.load(filename)
    
    def __contains__(self, key):
        return key in self._data
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
    
    def __setitem__(self, key, val):
        if key == READ_ORDER_KEY or key == LONGEST_KEY:
            raise KeyError("Please don't use READ_ORDER_KEY or LONGEST_KEY.")
        
        if isinstance(val, StorageList):
            val.parent = self
            val = val._list
        
        elif isinstance(val, StorageSet):
            val.parent = self
            val = val._data
        
        elif isinstance(val, bool):
            if val:
                val = u'yes'
            else:
                val = u'no'
        
        elif isinstance(val, float) or isinstance(val, int) or \
                isinstance(val, long):
            val = unicode(val)
        
        elif not isinstance(val, basestring):
            raise TypeError("Invalid value type!")
        
        if isinstance(val, str):
            try:
                val = unicode(val)
            except UnicodeDecodeError:
                pass
        
        self._data[key] = val
        self._modified()
    
    def __getitem__(self, key):
        if key == READ_ORDER_KEY or key == LONGEST_KEY:
            raise KeyError("Please don't use READ_ORDER_KEY or LONGEST_KEY.")
        val = self._data[key]
        if isinstance(val, list):
            val = StorageList(list=val, parent=self)
        elif isinstance(val, dict):
            val = StorageSet(data=val, parent=self)
        elif isinstance(val, str):
            pass
        elif val == u'yes':
            val = True
        elif val == u'no':
            val = False
        elif val.isdigit():
            val = int(val)
        elif val.replace('.','').isdigit():
            val = float(val)
        
        return val
    
    def __delitem__(self, key):
        if key == READ_ORDER_KEY or key == LONGEST_KEY:
            raise KeyError("Please don't use READ_ORDER_KEY or LONGEST_KEY.")
        if READ_ORDER_KEY in self._data and key in self._data[READ_ORDER_KEY]:
            self._data[READ_ORDER_KEY].remove(key)
        
        del self._data[key]
        self._modified()
    
    def __iter__(self):
        return (x for x in self._data if not x == READ_ORDER_KEY and not x == LONGEST_KEY)
    
    def _modified(self):
        self.modified = True
        if self.parent:
            self.parent._modified()
    
    def close(self):
        pass
    
    def contains(self, key):
        return key in self._data
    
    def keys(self):
        return list(self)
    
    def readBool(self, key):
        if not key in self._data:
            return False
        val = self._data[key]
        if val == u'yes':
            val = True
        elif val == u'no':
            val = False
        else:
            val = bool(val)
        return val
    
    def readDouble(self, key):
        if not key in self._data:
            return 0.0
        return float(self._data[key])
    
    def readInt(self, key):
        if not key in self._data:
            return 0
        return int(self._data[key])
    
    def readList(self, key):
        if not key in self._data:
            return StorageList(parent=self)
        return StorageList(list=self._data[key], parent=self)
    
    def readSet(self, key):
        if not key in self._data:
            return StorageSet(parent=self)
        return StorageSet(data=self._data[key], parent=self)
    
    def readString(self, key):
        if not key in self._data:
            return u""
        return self._data[key]
    
    def storeBool(self, key, val):
        if val:
            self._data[key] = u'yes'
        else:
            self._data[key] = u'no'
        self._modified()
    
    def storeDouble(self, key, val):
        self._data[key] = float(val)
        self._modified()
    
    def storeInt(self, key, val):
        self._data[key] = int(val)
        self._modified()
    
    def storeList(self, key, val):
        if not isinstance(val, StorageList):
            raise TypeError("Value must be a StorageList.")
        self._data[key] = val._list
        val.parent = self
        self._modified()
    
    def storeSet(self, key, val):
        if not isinstance(val, StorageSet):
            raise TypeError("Value must be a StorageSet.")
        self._data[key] = val
        val.parent = self
        self._modified()
    
    def storeString(self, key, val):
        self._data[key] = unicode(val)
        self._modified()
    
    def write(self, filename):
        """ Write the contents of a storage set to the specified file name. """
        with open(filename, 'wb') as f:
            self._write_set(f, 0, self._data)
    
    def _write_set(self, file, indentation, data):
        """ Write a storage set to a file. """
        longest = 0
        
        if LONGEST_KEY in data:
            longest = data[LONGEST_KEY]
        
        for key in data:
            if key == READ_ORDER_KEY or key == LONGEST_KEY:
                continue
            longest = max(longest, len(key))
        
        fmt = " "*indentation + "%%-%ds:%%s%%s\n" % longest
        
        if READ_ORDER_KEY in data:
            key_order = data[READ_ORDER_KEY]
            for key in data:
                if key == READ_ORDER_KEY or key == LONGEST_KEY:
                    continue
                if not key in key_order:
                    key_order.append(key)
        else:
            key_order = sorted(data.keys())
            if LONGEST_KEY in key_order:
                key_order.remove(LONGEST_KEY)
        
        for key in key_order:
            if isinstance(data[key], list):
                dtype = LIST_MARKER
                dat = ''
            elif isinstance(data[key], basestring) and ('\n' in data[key] or '\r' in data[key]):
                dtype = STRING_MARKER
                dat = ''
            elif isinstance(data[key], dict):
                dtype = SET_MARKER
                dat = ''
            else:
                dtype = TYPELESS_MARKER
                dat = data[key]
            
            if not isinstance(dat, basestring):
                dat = str(dat)
            elif isinstance(dat, unicode):
                dat = dat.encode(ENCODING)
            
            file.write(fmt % (key, dtype, dat))
            
            if dtype == LIST_MARKER:
                for set in data[key]:
                    self._write_set(file, indentation+INDENT_RATE, set)
            
            elif dtype == SET_MARKER:
                self._write_set(file, indentation+INDENT_RATE, data[key])
            
            elif dtype == STRING_MARKER:
                self._write_string(file, indentation+INDENT_RATE, data[key])
        
        file.write(" "*indentation + SET_MARKER + '\n')
    
    def _write_string(self, file, indentation, data):
        """ Write a string to a storage set file. """
        if isinstance(data, unicode):
            data = data.encode(ENCODING)
        
        indent = ' '*indentation
        
        for line in data.split('\n'):
            file.write(indent + line + '\n')
    
    def load(self, filename):
        """ Load the contents of a storage set from the specified file name. """
        with open(filename, 'rb') as f:
            self._read_set(PeekFile(f), 0, self._data)
    
    def _read_set(self, file, indentation, to):
        """ Read a set from a file. """
        read_order = []
        longest = 0
        to[READ_ORDER_KEY] = read_order
        
        while True:
            line = file.peekline()
            if not line:
                break
            indent = len(line) - len(line.lstrip())
            if indent != indentation:
                break
            
            line = file.readline()[indentation:].rstrip('\n')
            
            if line == SET_MARKER:
                break
            
            elif ':' in line:
                key, data = line.split(':',1)
                longest = max(longest, len(key.lstrip()))
                key = key.strip()
                dtype = data[0]
                data = data[1:]
                
                read_order.append(key)
                
                if dtype == TYPELESS_MARKER:
                    # This is the easy, inline one.
                    try:
                        to[key] = data.decode(ENCODING)
                    except UnicodeDecodeError:
                        to[key] = data
                
                elif dtype == LIST_MARKER:
                    to[key] = []
                    self._read_list(file, indentation+INDENT_RATE, to[key])
                
                elif dtype == STRING_MARKER:
                    to[key] = self._read_string(file, indentation+INDENT_RATE)
                
                elif dtype == SET_MARKER:
                    to[key] = {}
                    self._read_set(file, indentation+INDENT_RATE, to[key])
                
                else:
                    raise NotImplementedError
            
            else:
                raise ValueError("Bad set data.")
        
        to[LONGEST_KEY] = longest
    
    def _read_list(self, file, indentation, to):
        """ Read a StorageList from a file. """
        while True:
            line = file.peekline()
            if not line:
                break
            indent = len(line) - len(line.lstrip())
            if indent != indentation:
                break
            
            data = {}
            self._read_set(file, indentation, data)
            to.append(data)
    
    def _read_string(self, file, indentation):
        """ Read a string from a file. """
        data = ''
        while True:
            line = file.peekline()
            if not line:
                break
            indent = len(line) - len(line.lstrip())
            if indent < indentation:
                break
            
            data += file.readline()[indentation:]
        
        # Now try decoding it.
        if data.endswith('\n'):
            data = data[:-1]
            
        try:
            data = data.decode(ENCODING)
        except UnicodeDecodeError:
            pass
        
        return data
