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

"""Tests for dashboard_builder."""

import mock
import unittest

from compatibility_lib import compatibility_store
from compatibility_lib import fake_compatibility_store
from compatibility_lib import package

import dashboard_builder

PACKAGE_1 = package.Package("package1")
PACKAGE_2 = package.Package("package2")
PACKAGE_3 = package.Package("package3")


class _DeprecatedDepFinder(object):

    def get_deprecated_deps(self, packages=None):
        deprecated_deps = [
            (('gsutil', ['gcs-oauth2-boto-plugin', 'oauth2client']),),
            (('opencensus', []),),
            (('package1', []),),
            (('package2', []),),
            (('package3', ['deprecated_dep1', 'deprecated_dep2']),),
            (('gcloud', ['oauth2client']),)]

        return deprecated_deps

class TestResultHolderGetResult(unittest.TestCase):
    """Tests for dashboard_builder._ResultHolder.get_result()."""
    patch_finder = mock.patch('dashboard_builder.deprecated_dep_finder.DeprecatedDepFinder', _DeprecatedDepFinder)

    def test_self_compatibility_success(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )]
        }

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results, pairwise_to_results={})

        expected = {
            'status_type': 'self-success',
            'self_compatibility_check': [
                {'status': 'SUCCESS', 'self': True}],
            'pairwise_compatibility_check': []
        }
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_1),
            expected)

    def test_self_compatibility_error(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                details='Installation failure',
            )]
        }

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results, pairwise_to_results={})
        expected = {
            'status_type': 'self-install_error',
            'self_compatibility_check': [
                {'status': 'INSTALL_ERROR',
                 'self': True,
                 'details': 'Installation failure'
                 },
                {'status': 'INSTALL_ERROR',
                 'self': True,
                 'details': 'Installation failure'
                 },
            ],
            'pairwise_compatibility_check': []
        }
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_1),
            expected)

    def test_self_compatibility_no_entry(self):
        package_to_results = {PACKAGE_1: []}

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results, pairwise_to_results={})

        expected = {
            'status_type': 'self-unknown',
            'self_compatibility_check': [
                {'status': 'UNKNOWN', 'self': True},
            ],
            'pairwise_compatibility_check': []
        }
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_1),
            expected)

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

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results,
                pairwise_to_results=pairwise_to_results)

        expected = {
            'status_type': 'pairwise-success',
            'self_compatibility_check': [],
            'pairwise_compatibility_check': [
                {'status': 'SUCCESS', 'self': False}
            ]
        }
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_2),
            expected)

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

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results,
                pairwise_to_results=pairwise_to_results)
        expected = {
            'status_type': 'pairwise-install_error',
            'self_compatibility_check': [],
            'pairwise_compatibility_check': [
                {'status': 'INSTALL_ERROR',
                 'self': False,
                 'details': 'Installation failure'
                 }
            ]
        }
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_2),
            expected)

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

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results,
                pairwise_to_results=pairwise_to_results)
        expected = {
            'status_type': 'pairwise-unknown',
            'self_compatibility_check': [],
            'pairwise_compatibility_check': [
                {'status': 'UNKNOWN', 'self': False}
            ]
        }
        self.assertEqual(
            rh.get_result(PACKAGE_1, PACKAGE_2),
            expected)


class TestResultHolderHasIssues(unittest.TestCase):
    """Tests for dashboard_builder._ResultHolder.has_issues()."""
    patch_finder = mock.patch(
        'dashboard_builder.deprecated_dep_finder.DeprecatedDepFinder',
        _DeprecatedDepFinder)

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

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results,
                pairwise_to_results=pairwise_to_results)
        self.assertFalse(rh.has_issues(PACKAGE_1))
        self.assertFalse(rh.has_issues(PACKAGE_2))

    def test_self_issues(self):
        package_to_results = {
            PACKAGE_1: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1],
                python_major_version=3,
                status=compatibility_store.Status.CHECK_WARNING,
                details='Self Conflict',
            )],
            PACKAGE_2: [compatibility_store.CompatibilityResult(
                packages=[PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS,
            )],
        }
        pairwise_to_results = {
            frozenset([PACKAGE_1, PACKAGE_2]): [
                compatibility_store.CompatibilityResult(
                    packages=[PACKAGE_1, PACKAGE_2],
                    python_major_version=3,
                    status=compatibility_store.Status.CHECK_WARNING,
                    details='Conflict',
                )],
        }

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
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

        with self.patch_finder:
            rh = dashboard_builder._ResultHolder(
                package_to_results=package_to_results,
                pairwise_to_results=pairwise_to_results)
        self.assertTrue(rh.has_issues(PACKAGE_1))
        self.assertTrue(rh.has_issues(PACKAGE_2))


class TestGridBuilder(unittest.TestCase):
    """Tests for dashboard_builder.GridBuilder."""
    patch_finder = mock.patch(
        'dashboard_builder.deprecated_dep_finder.DeprecatedDepFinder',
        _DeprecatedDepFinder)

    def test_success(self):
        """CompatibilityResult available for all packages and pairs."""
        packages = [PACKAGE_1, PACKAGE_2]
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
        with self.patch_finder:
            package_to_results = store.get_self_compatibilities(packages)
            pairwise_to_results = store.get_compatibility_combinations(
                packages)
            results = dashboard_builder._ResultHolder(package_to_results,
                                                      pairwise_to_results)
            builder = dashboard_builder.DashboardBuilder(packages, results)
            builder.build_dashboard('dashboard/grid-template.html')

    def test_self_failure(self):
        """CompatibilityResult failure installing a single package."""
        packages = [PACKAGE_1, PACKAGE_2]
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

        with self.patch_finder:
            package_to_results = store.get_self_compatibilities(packages)
            pairwise_to_results = store.get_compatibility_combinations(
                packages)
            results = dashboard_builder._ResultHolder(package_to_results,
                                                      pairwise_to_results)
            builder = dashboard_builder.DashboardBuilder(packages, results)
            html_grid = builder.build_dashboard('dashboard/grid-template.html')
            self.assertIn("Installation failure", html_grid)

    def test_missing_pairwise(self):
        """CompatibilityResult not available for a pair of packages."""
        packages = [PACKAGE_1, PACKAGE_2]
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

        with self.patch_finder:
            package_to_results = store.get_self_compatibilities(packages)
            pairwise_to_results = store.get_compatibility_combinations(
                packages)
            results = dashboard_builder._ResultHolder(package_to_results,
                                                      pairwise_to_results)
            builder = dashboard_builder.DashboardBuilder(packages, results)
            builder.build_dashboard('dashboard/grid-template.html')

    def test_missing_self(self):
        """CompatibilityResult not available for individual packages."""
        packages = [PACKAGE_1, PACKAGE_2]
        store = fake_compatibility_store.CompatibilityStore()
        store.save_compatibility_statuses([
            compatibility_store.CompatibilityResult(
                packages=[PACKAGE_1, PACKAGE_2],
                python_major_version=3,
                status=compatibility_store.Status.SUCCESS
            ),
        ])

        with self.patch_finder:
            package_to_results = store.get_self_compatibilities(packages)
            pairwise_to_results = store.get_compatibility_combinations(
                packages)
            results = dashboard_builder._ResultHolder(package_to_results,
                                                      pairwise_to_results)
            builder = dashboard_builder.DashboardBuilder(packages, results)
            builder.build_dashboard('dashboard/grid-template.html')

    def test_pairwise_failure(self):
        """CompatibilityResult failure between pair of packages."""
        packages = [PACKAGE_1, PACKAGE_2]
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

        with self.patch_finder:
            package_to_results = store.get_self_compatibilities(packages)
            pairwise_to_results = store.get_compatibility_combinations(
                packages)
            results = dashboard_builder._ResultHolder(package_to_results,
                                                      pairwise_to_results)
            builder = dashboard_builder.DashboardBuilder(packages, results)
            html_grid = builder.build_dashboard('dashboard/grid-template.html')
            self.assertIn("Installation failure", html_grid)

    def test_not_show_py_ver_incompatible_results(self):
        """CompatibilityResult failure between pair of packages. Do not display
        the packages that are incompatible with a specific Python version.
        """
        packages = [PACKAGE_1, PACKAGE_2]
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

        with patch, self.patch_finder:
            package_to_results = store.get_self_compatibilities(packages)
            pairwise_to_results = store.get_compatibility_combinations(
                packages)
            results = dashboard_builder._ResultHolder(package_to_results,
                                                      pairwise_to_results)

            builder = dashboard_builder.DashboardBuilder(packages, results)
            html_grid = builder.build_dashboard('dashboard/grid-template.html')

        self.assertNotIn("Installation failure", html_grid)
