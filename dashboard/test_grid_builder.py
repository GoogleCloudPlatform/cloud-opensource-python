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

"""Tests for grid_builder."""

import mock
import unittest

from compatibility_lib import compatibility_store
from compatibility_lib import fake_compatibility_store
from compatibility_lib import package

import grid_builder

PACKAGE_1 = package.Package("package1")
PACKAGE_2 = package.Package("package2")
PACKAGE_3 = package.Package("package3")


class TestResultHolderGetResult(unittest.TestCase):
    """Tests for grid_builder._ResultHolder.get_result()."""

    def test_self_compatibility_success(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results, pairwise_to_results={})
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_1),
            {'status': 'SUCCESS', 'self': True})

    def test_self_compatibility_error(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                details='Installation failure',
            )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results, pairwise_to_results={})
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_1),
            {'status': 'INSTALL_ERROR', 'details': 'Installation failure',
             'self': True})

    def test_self_compatibility_no_entry(self):
        package_to_results = {PACKAGE_1: []}
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results, pairwise_to_results={})
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_1),
            {'status': 'UNKNOWN', 'self': True})

    def test_pairwise_success(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): [
                compatibility_store.CompatibilityResult(
                    packages=[PACKAGE_1, PACKAGE_2],
                    python_major_version=3,
                    status=compatibility_store.Status.SUCCESS,
                )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results,
            pairwise_to_results=pairwise_to_results)
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_2),
            {'status': 'SUCCESS', 'self': False})

    def test_pairwise_error(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): [
                compatibility_store.CompatibilityResult(
                    packages=[PACKAGE_1, PACKAGE_2],
                    python_major_version=3,
                    status=compatibility_store.Status.INSTALL_ERROR,
                    details='Installation failure',
                )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results,
            pairwise_to_results=pairwise_to_results)
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_2),
            {'status': 'INSTALL_ERROR', 'details': 'Installation failure',
             'self': False})

    def test_pairwise_no_entry(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): []
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results,
            pairwise_to_results=pairwise_to_results)
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_2),
            {'status': 'UNKNOWN', 'self': False})


class TestResultHolderHasIssues(unittest.TestCase):
    """Tests for grid_builder._ResultHolder.has_issues()."""

    def test_no_issues(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): [
                compatibility_store.CompatibilityResult(
                    packages=[PACKAGE_1, PACKAGE_2],
                    python_major_version=3,
                    status=compatibility_store.Status.SUCCESS,
                )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results,
            pairwise_to_results=pairwise_to_results)
        self.assertFalse(rh.has_issues(PACKAGE_1))
        self.assertFalse(rh.has_issues(PACKAGE_2))

    def test_self_issues(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                details='Installation failure',
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): [
                compatibility_store.CompatibilityResult(
                    packages=[PACKAGE_1, PACKAGE_2],
                    python_major_version=3,
                    status=compatibility_store.Status.INSTALL_ERROR,
                    details='Installation failure',
                )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results,
            pairwise_to_results=pairwise_to_results)
        self.assertTrue(rh.has_issues(PACKAGE_1))
        self.assertFalse(rh.has_issues(PACKAGE_2))

    def test_pairwise_issues(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): [
                compatibility_store.CompatibilityResult(
                    packages=[PACKAGE_1, PACKAGE_2],
                    python_major_version=3,
                    status=compatibility_store.Status.INSTALL_ERROR,
                    details='Installation failure',
                )]
        }
        rh = grid_builder._ResultHolder(
            package_to_results=package_to_results,
            pairwise_to_results=pairwise_to_results)
        self.assertTrue(rh.has_issues(PACKAGE_1))
        self.assertTrue(rh.has_issues(PACKAGE_2))


class TestGridBuilder(unittest.TestCase):
    """Tests for grid_builder.GridBuilder."""

    def test_success(self):
        """CompatibilityResult available for all packages and pairs."""
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

    def test_self_failure(self):
        """CompatibilityResult failure installing a single package."""
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                details="Installation failure"
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
        ])
        grid = grid_builder.GridBuilder(store)
        html_grid = grid.build_grid([PACKAGE_1, PACKAGE_2])
        self.assertIn("Installation failure", html_grid)

    def test_missing_pairwise(self):
        """CompatibilityResult not available for a pair of packages."""
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
        """CompatibilityResult not available for individual packages."""
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1, PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
        ])
        grid = grid_builder.GridBuilder(store)
        grid.build_grid([PACKAGE_1, PACKAGE_2])

    def test_pairwise_failure(self):
        """CompatibilityResult failure between pair of packages."""
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
                status=compatibility_store.Status.INSTALL_ERROR,
                details="Installation failure"
            ),
        ])
        grid = grid_builder.GridBuilder(store)
        html_grid = grid.build_grid([PACKAGE_1, PACKAGE_2])
        self.assertIn("Installation failure", html_grid)

    def test_not_show_py_ver_incompatible_results(self):
        """CompatibilityResult failure between pair of packages. Do not display
        the packages that are incompatible with a specific Python version.
        """
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_3],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR
            ),
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1, PACKAGE_3],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                details="Installation failure"
            ),
        ])
        patch = mock.patch(
            'compatibility_lib.configs.PKG_PY_VERSION_NOT_SUPPORTED', {
            2: ['package4'],
            3: ['package3'],
        })

        with patch:
            grid = grid_builder.GridBuilder(store)
            html_grid = grid.build_grid([PACKAGE_1, PACKAGE_2])

        self.assertNotIn("Installation failure", html_grid)
