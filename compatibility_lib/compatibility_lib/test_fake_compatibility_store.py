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

"""Tests for compatibility_store.CompatibilityStore."""

import datetime
import unittest

from compatibility_lib import compatibility_store
from compatibility_lib import fake_compatibility_store
from compatibility_lib import package

PACKAGE_1 = package.Package("package1")
PACKAGE_2 = package.Package("package2")
PACKAGE_3 = package.Package("package3")
PACKAGE_4 = package.Package("package4")

PACKAGE_1_PY2_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_1],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_1_PY2_OLD_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_1],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2018, 1, 1),
)

PACKAGE_1_PY3_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_1],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_2_PY2_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_2],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_2_PY3_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_2],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_3_PY2_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_3],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_3_PY3_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_3],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_1_AND_2_PY2_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_1, PACKAGE_2],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
)

PACKAGE_1_AND_2_PY2_OLD_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_1, PACKAGE_2],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2018, 1, 1),
)

PACKAGE_1_AND_2_PY3_CR = compatibility_store.CompatibilityResult(
    packages=[PACKAGE_1, PACKAGE_2],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
)


class TestCompatibilityStore(unittest.TestCase):

    def setUp(self):
        self._store = fake_compatibility_store.CompatibilityStore()

    def test_get_self_compatibility(self):
        crs = [PACKAGE_1_PY2_CR, PACKAGE_1_PY2_OLD_CR, PACKAGE_1_PY3_CR,
               PACKAGE_2_PY2_CR]
        self._store.save_compatibility_statuses(crs)
        self.assertEqual(
            frozenset(self._store.get_self_compatibility(PACKAGE_1)),
            frozenset([PACKAGE_1_PY2_CR, PACKAGE_1_PY3_CR]))
        self.assertEqual(
            frozenset(self._store.get_self_compatibility(PACKAGE_2)),
            frozenset([PACKAGE_2_PY2_CR]))

    def test_get_self_compatibility_no_result(self):
        crs = [PACKAGE_1_PY2_CR, PACKAGE_1_PY2_OLD_CR, PACKAGE_1_PY3_CR,
               PACKAGE_2_PY2_CR,
               PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)
        self.assertFalse(
            frozenset(self._store.get_self_compatibility(PACKAGE_3)))

    def test_get_self_compatibilities(self):
        crs = [PACKAGE_1_PY2_CR, PACKAGE_1_PY2_OLD_CR, PACKAGE_1_PY3_CR,
               PACKAGE_2_PY2_CR,
               PACKAGE_3_PY2_CR, PACKAGE_3_PY3_CR,
               PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)
        self.assertEqual(
            self._store.get_self_compatibilities([PACKAGE_1, PACKAGE_2]),
            {
                PACKAGE_1: [PACKAGE_1_PY2_CR, PACKAGE_1_PY3_CR],
                PACKAGE_2: [PACKAGE_2_PY2_CR]
            })

    def test_get_self_compatibilities_no_results(self):
        crs = [PACKAGE_1_PY2_CR, PACKAGE_1_PY2_OLD_CR, PACKAGE_1_PY3_CR,
               PACKAGE_2_PY2_CR,
               PACKAGE_3_PY2_CR, PACKAGE_3_PY3_CR,
               PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)
        self.assertEqual(
            self._store.get_self_compatibilities(
                [PACKAGE_1, PACKAGE_2, PACKAGE_4]),
            {
                PACKAGE_1: [PACKAGE_1_PY2_CR, PACKAGE_1_PY3_CR],
                PACKAGE_2: [PACKAGE_2_PY2_CR],
                PACKAGE_4: [],
            })

    def test_get_pair_compatibility(self):
        crs = [PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY2_OLD_CR,
               PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)

        self.assertEqual(
            frozenset(
                self._store.get_pair_compatibility([PACKAGE_1, PACKAGE_2])),
            frozenset([PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY3_CR]))

    def test_get_pair_compatibility_no_results(self):
        crs = [PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)

        self.assertFalse(
            frozenset(
                self._store.get_pair_compatibility([PACKAGE_1, PACKAGE_3])))

    def test_get_compatibility_combinations(self):
        crs = [PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY2_OLD_CR,
               PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)

        self.assertEqual(
            frozenset(self._store.get_compatibility_combinations(
                [PACKAGE_1, PACKAGE_2])),
            frozenset({frozenset([PACKAGE_1, PACKAGE_2]): [
                PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY3_CR]})
        )

    def test_get_compatibility_combinations_no_results(self):
        crs = [PACKAGE_1_AND_2_PY2_CR, PACKAGE_1_AND_2_PY2_OLD_CR,
               PACKAGE_1_AND_2_PY3_CR]
        self._store.save_compatibility_statuses(crs)

        self.assertEqual(
            frozenset(self._store.get_compatibility_combinations(
                [PACKAGE_1, PACKAGE_2, PACKAGE_3])),
            frozenset({
                frozenset([PACKAGE_1, PACKAGE_2]): [PACKAGE_1_AND_2_PY2_CR,
                                                    PACKAGE_1_AND_2_PY3_CR],
                frozenset([PACKAGE_1, PACKAGE_3]): [],
                frozenset([PACKAGE_2, PACKAGE_3]): [],
            }))
