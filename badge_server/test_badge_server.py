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

import mock
import unittest

from compatibility_lib import fake_compatibility_store

import badge_server


class TestBadgeServer(unittest.TestCase):

    def setUp(self):
        self.mock_checker = mock.Mock(autospec=True)
        self.fake_store = fake_compatibility_store.CompatibilityStore()
        self.patch_checker = mock.patch(
            'badge_server.checker', self.mock_checker)
        self.patch_store = mock.patch('badge_server.store', self.fake_store)

    def test__get_pair_status_for_packages_success(self):
        pkg_sets = [
            ['opencensus', 'google-api-core'],
            ['opencensus', 'google-api-python-client']
        ]
        expected = {
            'py2': {'status': 'SUCCESS', 'details': {}},
            'py3': {'status': 'SUCCESS', 'details': {}}
        }

        with self.patch_checker, self.patch_store:
            version_and_res = badge_server._get_pair_status_for_packages(
                pkg_sets)

        self.assertEqual(version_and_res, expected)

    def test__get_pair_status_for_packages_warning(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        PACKAGE_1 = package.Package("package1")
        PACKAGE_2 = package.Package("package2")

        pkg_sets = [
            ['package1', 'package2'],
        ]
        expected = {
            'py2': {
                'status': 'CHECK_WARNING',
                'details': {'package2': 'NO DETAILS'}
            },
            'py3': {
                'status': 'CHECK_WARNING',
                'details': {'package2': 'NO DETAILS'}
            }
        }
        cr_py2 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1, PACKAGE_2],
            python_major_version=2,
            status=compatibility_store.Status.CHECK_WARNING)
        cr_py3 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1, PACKAGE_2],
            python_major_version=3,
            status=compatibility_store.Status.CHECK_WARNING)
        pair_result = [cr_py2, cr_py3]
        self.fake_store._packages_to_compatibility_result[
            frozenset([PACKAGE_1, PACKAGE_2])] = pair_result

        with self.patch_checker, self.patch_store:
            version_and_res = badge_server._get_pair_status_for_packages(
                pkg_sets)

        self.assertEqual(version_and_res, expected)

    def test__get_pair_status_for_packages_install_error(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        PACKAGE_1 = package.Package("package1")
        PACKAGE_2 = package.Package("tensorflow")

        pkg_sets = [
            ['package1', 'tensorflow'],
        ]
        expected = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }
        cr_py2 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1, PACKAGE_2],
            python_major_version=2,
            status=compatibility_store.Status.INSTALL_ERROR)
        cr_py3 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1, PACKAGE_2],
            python_major_version=3,
            status=compatibility_store.Status.SUCCESS)
        pair_result = [cr_py2, cr_py3]
        self.fake_store._packages_to_compatibility_result[
            frozenset([PACKAGE_1, PACKAGE_2])] = pair_result

        with self.patch_checker, self.patch_store:
            version_and_res = badge_server._get_pair_status_for_packages(
                pkg_sets)

        self.assertEqual(version_and_res, expected)

    def test__get_pair_status_for_packages_self_conflict(self):
        # If the pair package is not self compatible, the package being checked
        # should not be marked as CHECK_WARNING.
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        PACKAGE_1 = package.Package("package1")
        PACKAGE_2 = package.Package("tensorflow")

        pkg_sets = [
            ['package1', 'tensorflow'],
        ]
        expected = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }
        cr_py2 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1, PACKAGE_2],
            python_major_version=2,
            status=compatibility_store.Status.CHECK_WARNING)
        cr_py3 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1, PACKAGE_2],
            python_major_version=3,
            status=compatibility_store.Status.CHECK_WARNING)
        pair_result = [cr_py2, cr_py3]
        self.fake_store._packages_to_compatibility_result[
            frozenset([PACKAGE_1, PACKAGE_2])] = pair_result

        mock_self_res = mock.Mock()
        self_res = {
            'py2': {
                'status': 'CHECK_WARNING', 'details': {}
            },
            'py3': {
                'status': 'CHECK_WARNING', 'details': {}
            }
        }
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'badge_server._get_self_compatibility_from_cache',
            mock_self_res)

        with self.patch_checker, self.patch_store, patch_self_status:
            version_and_res = badge_server._get_pair_status_for_packages(
                pkg_sets)

        self.assertEqual(version_and_res, expected)

    def test__sanitize_package_name(self):
        package_name = 'google-cloud-trace'
        expected = 'google.cloud.trace'

        sanitized = badge_server._sanitize_package_name(package_name)
        self.assertEqual(sanitized, expected)

    def test__sanitize_package_name_github(self):
        package_name = 'git+git://github.com/GoogleCloudPlatform/cloud-opensource-python.git#subdirectory=compatibility_lib'
        expected = 'github head'

        sanitized = badge_server._sanitize_package_name(package_name)
        self.assertEqual(sanitized, expected)

    def test__get_badge_url_use_py2(self):
        package_name = 'package-1'
        res = {
            'py2': {
                'status': 'CHECK_WARNING', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }

        url = badge_server._get_badge_url(res, package_name)
        expected = 'https://img.shields.io/badge/package.1-CHECK_WARNING-red.svg'

        self.assertEqual(url, expected)

    def test__get_badge_url_use_py3(self):
        package_name = 'package-1'
        res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'CHECK_WARNING', 'details': {}
            }
        }

        url = badge_server._get_badge_url(res, package_name)
        expected = 'https://img.shields.io/badge/package.1-CHECK_WARNING-red.svg'

        self.assertEqual(url, expected)

    def test__get_all_results_from_cache_success(self):
        self_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }
        mock_self_res = mock.Mock()
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'badge_server._get_self_compatibility_from_cache',
            mock_self_res)

        google_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }
        mock_google_res = mock.Mock()
        mock_google_res.return_value = google_res
        patch_google_status = mock.patch(
            'badge_server._get_google_compatibility_from_cache',
            mock_google_res)

        dep_res = {
            'status': 'UP_TO_DATE',
            'details': {},
        }
        mock_dep_res = mock.Mock()
        mock_dep_res.return_value = dep_res
        patch_dep_status = mock.patch(
            'badge_server._get_dependency_result_from_cache',
            mock_dep_res)

        with patch_self_status, patch_google_status, patch_dep_status:
            status, _, _, _ = badge_server._get_all_results_from_cache(
                'package1')

        self.assertEqual(status, 'SUCCESS')

    def test__get_all_results_from_cache_calculating(self):
        self_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }
        mock_self_res = mock.Mock()
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'badge_server._get_self_compatibility_from_cache',
            mock_self_res)

        google_res = {
            'py2': {
                'status': 'CALCULATING', 'details': {}
            },
            'py3': {
                'status': 'CALCULATING', 'details': {}
            }
        }
        mock_google_res = mock.Mock()
        mock_google_res.return_value = google_res
        patch_google_status = mock.patch(
            'badge_server._get_google_compatibility_from_cache',
            mock_google_res)

        dep_res = {
            'status': 'UP_TO_DATE',
            'details': {},
        }
        mock_dep_res = mock.Mock()
        mock_dep_res.return_value = dep_res
        patch_dep_status = mock.patch(
            'badge_server._get_dependency_result_from_cache',
            mock_dep_res)

        with patch_self_status, patch_google_status, patch_dep_status:
            status, _, _, _ = badge_server._get_all_results_from_cache(
                'package1')

        self.assertEqual(status, 'CALCULATING')

    def test__get_all_results_from_cache_check_warning(self):
        self_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }
        mock_self_res = mock.Mock()
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'badge_server._get_self_compatibility_from_cache',
            mock_self_res)

        google_res = {
            'py2': {
                'status': 'CHECK_WARNING', 'details': {}
            },
            'py3': {
                'status': 'CHECK_WARNING', 'details': {}
            }
        }
        mock_google_res = mock.Mock()
        mock_google_res.return_value = google_res
        patch_google_status = mock.patch(
            'badge_server._get_google_compatibility_from_cache',
            mock_google_res)

        dep_res = {
            'status': 'UP_TO_DATE',
            'details': {},
        }
        mock_dep_res = mock.Mock()
        mock_dep_res.return_value = dep_res
        patch_dep_status = mock.patch(
            'badge_server._get_dependency_result_from_cache',
            mock_dep_res)

        with patch_self_status, patch_google_status, patch_dep_status:
            status, _, _, _ = badge_server._get_all_results_from_cache(
                'package1')

        self.assertEqual(status, 'CHECK_WARNING')
