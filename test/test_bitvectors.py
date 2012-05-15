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
This file contains tests for the bitvectors module.
"""

###############################################################################
# Imports
###############################################################################

from nakedsun import bitvectors

###############################################################################
# The Tests
###############################################################################

def test_create():
    # Just create a bitvector
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    assert "something_else" in bitvectors.bitvectors

def test_instance():
    # Instance a Bitvector
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    b = bitvectors.Bitvector("something_else")

    assert b.one is False
    assert b.two is False

def test_set():
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    b = bitvectors.Bitvector("something_else")

    assert b.one is False
    b.one = True
    assert b.one is True

def test_any():
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    b = bitvectors.Bitvector("something_else")

    assert b.any() is False
    b.one = True
    assert b.any() is True

def test_setall():
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    b = bitvectors.Bitvector("something_else")

    assert b.one is False
    assert b.two is False

    b.setall(True)

    assert b.one is True
    assert b.two is True

def test_str():
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    b = bitvectors.Bitvector("something_else")

    assert str(b) == ""
    b.one = True
    assert str(b) == "one"
    b.two = True
    assert str(b) == "one, two"

def test_fromstr():
    bitvectors.bitvectors = {}
    bitvectors.create_bitvector("something_else", "one", "two")

    b = bitvectors.Bitvector("something_else", "one")

    assert b.one is True
    assert b.two is False

    b = bitvectors.Bitvector("something_else", "one, two")

    assert b.one is True
    assert b.two is True
