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
This module loads and saves basic MUD settings.
"""

###############################################################################
# Imports
###############################################################################

import json
import os
import sys

from . import hooks
from . import logger as log

###############################################################################
# Storage and Constants
###############################################################################

_settings = {}
_source = None
_path = None

###############################################################################
# Initialization
###############################################################################

def initialize():
    """
    Load the MUD settings and initialize the appropriate storage module,
    depending on how the settings are stored.
    """
    global _settings
    global _source
    global _path

    # First, check for a new-style config file containing JSON.
    if os.path.exists('config'):
        with file('config', 'rb') as f:
            _settings.update(json.load(f))
        _source = 'config'
        _path = os.path.abspath('config')

    elif os.path.exists('muddata'):
        log.warning(u"Using default configuration for a NakedMud library.")

        _settings['storage_engine'] = u"nakedmud"
        _settings['password_hashing'] = u"nmcompat"
        _settings['template_engine'] = u"nakedmud"
        _settings['nakedmud_compatible'] = True
        _source = 'muddata'
        _path = os.path.abspath('muddata')

        from . import storage
        with storage.StorageSet('muddata') as storage_set:
            for key in storage_set:
                _settings[key] = storage_set[key]

    else:
        log.error(u"Unable to find a MUD configuration file.")
        sys.exit(1)

    ## Password Salt Generation

    if not get('password_salt'):
        import time
        import hashlib

        salt = ""
        while len(salt) < 64:
            salt += hashlib.sha1("%s%s%s" % (time.time(),
                                        os.getcwd(), os.urandom(64))).digest()

        set('password_salt', salt, False)

    ## Default Values

    if not get('pulses_per_second'):
        set('pulses_per_second', 10, False)

    if not get('start_room'):
        if get('nakedmud_compatible'):
            set('start_room', 'tavern_entrance@examples', False)
        else:
            set('start_room', 'house@examples', False)

    if not get('main_addr'):
        set('main_addr', ':4000', False)

    # Save for fun.
    save_settings()

###############################################################################
# Getters and Setters
###############################################################################

get = _settings.get
has_key = _settings.has_key
keys = _settings.keys

def set(key, val, autosave=True):
    _settings[key] = val
    hooks.run("setting_changed", key, val)
    if autosave:
        save_settings()

def save_settings():
    """ Save the MUD settings back to file. """
    if _source == 'config':
        with open(_path, 'wb') as f:
            json.dump(_settings, f)

    elif _source == 'muddata':
        from . import storage
        storage_set = storage.StorageSet()
        for key in _settings:
            try:
                storage_set[key] = _settings[key]
            except TypeError:
                log.warning(u"Couldn't save MUD setting %r with value %r." %
                            (key, _settings[key]))
        storage_set.write(_path)
        storage_set.close()
