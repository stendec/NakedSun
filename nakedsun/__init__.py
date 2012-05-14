#!/usr/bin/env python
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
An easilly customizable MUD server written in Python that makes minimal
assumptions about the game you want to create, providing a bare framework on
which you can design anything you want without having to rip out useless
systems like pre-existing stats systems.
"""

###############################################################################
# Imports
###############################################################################

import nakedsun.bitvectors
import nakedsun.event
import nakedsun.hooks
import nakedsun.semver

###############################################################################
# Exports
###############################################################################

__authors__ = ["Stendec"]
__version__ = version = nakedsun.semver.Version("0.1.0-dev")
