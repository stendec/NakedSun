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
The storage package contains all the available storage engines for NakedSun and
automatically imports the appropriate engine when it's imported.
"""

###############################################################################
# Imports
###############################################################################

import nakedsun.settings

###############################################################################
# Logic
###############################################################################

# Get the storage module.
name = nakedsun.settings.get('storage_engine', 'nakedmud')
module = __import__(name, globals(), locals())

# Grab what we want.
StorageList = module.StorageList
StorageSet = module.StorageSet

# And only export what we want.
__all__ = ['StorageList', 'StorageSet']
