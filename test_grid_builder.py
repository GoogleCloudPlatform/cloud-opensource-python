# Copyright 2018 Google LLC
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

"""Tests for pip_checker.

Uses a script "fake_pip.py" to simulate the behavior of the pip
(https://pypi.org/project/pip/) installation tool.
"""

import unittest

from compatibility_lib import compatibility_store
from compatibility_lib import fake_compatibility_store
from compatibility_lib import package

import grid_builder


"""

def __init__(self,
             packages: Iterable[package.Package],
             python_major_version: int,
             status: Status = Status.UNKNOWN,
             details: Optional[str] = None,
             timestamp: Optional[datetime.datetime] = None):
"""

PACKAGE_1 = package.Package("package1")
PACKAGE_2 = package.Package("package2")
PACKAGE_3 = package.Package("package3")

class TestGridBuilder(unittest.TestCase):

    def test_success(self):
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1, PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
        ])
        grid = grid_builder.GridBuilder(store)
        grid.build_grid([PACKAGE_1, PACKAGE_2])

    def test_missing_pairwise(self):
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
        ])
        grid = grid_builder.GridBuilder(store)
        grid.build_grid([PACKAGE_1, PACKAGE_2])

    def test_missing_self(self):
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1, PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
        ])
        grid = grid_builder.GridBuilder(store)
        grid.build_grid([PACKAGE_1, PACKAGE_2])
