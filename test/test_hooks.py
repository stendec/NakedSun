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
This file contains tests for the hooks module.
"""

###############################################################################
# Imports
###############################################################################

from nakedsun import hooks

###############################################################################
# Initialization
###############################################################################

from nakedsun import logger as log

def dummy(*args, **kwargs):
    pass

log.log = log.info = log.debug = log.warning = log.error = log.critical = \
log.exception = dummy

###############################################################################
# The Tests
###############################################################################

def test_basic():
    values = []

    @hooks.hook("test_basic")
    def test(name):
        values.append(name)

    hooks.run("test_basic", "Bobby")
    hooks.run("test_basic", "Johnny")

    assert len(values) == 2
    assert values == ["Bobby", "Johnny"]

def test_compatibility():
    values = []

    def test(info):
        name, = hooks.parse_info(info)
        values.append(name)

    hooks.add("test_compatibility", test)

    hooks.run("test_compatibility", hooks.build_info("str", ("Bobby", )))
    hooks.run("test_compatibility", hooks.build_info("str", ("Johnny", )))

    assert len(values) == 2
    assert values == ["Bobby", "Johnny"]

def test_priority():
    values = []

    @hooks.hook("test_priority")
    def test(name):
        values.append(name)

    @hooks.hook("test_priority", priority=1)
    def tester(name):
        values.append("corn")

    hooks.run("test_priority", "Steve")

    assert len(values) == 2
    assert values == ["corn", "Steve"]

def test_stopprop():
    values = []

    @hooks.hook("test_stopprop")
    def test(name):
        values.append(name)

    @hooks.hook("test_stopprop", priority=1)
    def tester(name):
        raise StopIteration

    hooks.run("test_stopprop", "Bobby")
    hooks.run("test_stopprop", "Johnny")

    assert len(values) == 0

def test_info():
    test = 'some', 'list', 'of', 5, 'things'

    assert test == hooks.parse_info(hooks.build_info('', test))

def test_removal():
    def test(name):
        print name

    assert hooks.remove("test_removal", test) is False

    hooks.add("test_removal", test)

    assert hooks.remove("test_removal", test) is True
