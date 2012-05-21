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
This module contains the Obj class used for all objects within the
MUD, and functions to iterate over and work with those objects.
"""

###############################################################################
# Imports
###############################################################################

from . import auxiliary
from . import hooks
from . import logger as log

###############################################################################
# Char Class
###############################################################################

@auxiliary.register("object")
class Obj(auxiliary.AuxiliaryBase):
    pass
