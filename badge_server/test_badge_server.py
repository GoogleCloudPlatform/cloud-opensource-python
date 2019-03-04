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
import os
import unittest

from compatibility_lib import fake_compatibility_store

os.environ["RUN_LOCALLY"] = 'true'

# Set the cache to use local cache before importing the main module
import main


class TestBadgeServer(unittest.TestCase):

    def setUp(self):
        self.mock_checker = mock.Mock(autospec=True)
        self.fake_store = fake_compatibility_store.CompatibilityStore()
        self.patch_checker = mock.patch(
            'main.badge_utils.checker', self.mock_checker)
        self.patch_store = mock.patch(
            'main.badge_utils.store', self.fake_store)

    def test__get_self_compatibility_dict(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': {'status': 'SUCCESS', 'details':
                    'The package does not support this version of python.'},
            'py3': {'status': 'SUCCESS', 'details': 'NO DETAILS'},
        }

        PACKAGE = package.Package('tensorflow')
        cr_py3 = compatibility_store.CompatibilityResult(
            packages=[PACKAGE],
            python_major_version=3,
            status=compatibility_store.Status.SUCCESS)
        self.fake_store._packages_to_compatibility_result[
            frozenset([PACKAGE])] = [cr_py3]

        with self.patch_checker, self.patch_store:
            result_dict = main._get_self_compatibility_dict('tensorflow')

        self.assertEqual(result_dict, expected)

    def test__get_pair_compatibility_dict_success(self):
        expected = {
            'py2': {'status': 'SUCCESS', 'details': None},
            'py3': {'status': 'SUCCESS', 'details': None}
        }

        pkgs = ['google-api-core', 'google-api-python-client']
        patch_configs = mock.patch('main.configs.PKG_LIST', pkgs)
        with self.patch_checker, self.patch_store, patch_configs:
            result_dict = main._get_pair_compatibility_dict('opencensus')

        self.assertEqual(result_dict, expected)

    def test__get_pair_compatibility_dict_warning(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': {'status': 'CHECK_WARNING',
                    'details': {'package2': 'NO DETAILS'} },
            'py3': {'status': 'CHECK_WARNING',
                    'details': {'package2': 'NO DETAILS'} },
        }

        PACKAGE_1 = package.Package("package1")
        PACKAGE_2 = package.Package("package2")
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
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'main._get_self_compatibility_dict',
            mock_self_res)

        pkgs = ['package2']
        patch_configs = mock.patch('main.configs.PKG_LIST', pkgs)

        with self.patch_checker, self.patch_store, patch_self_status, \
                patch_configs:
            result_dict = main._get_pair_compatibility_dict(
                'package1')

        self.assertEqual(result_dict, expected)

    def test__get_pair_compatibility_dict_install_error(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }

        PACKAGE_1 = package.Package("package1")
        PACKAGE_2 = package.Package("tensorflow")
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

        pkgs = ['tensorflow']
        patch_configs = mock.patch('main.configs.PKG_LIST', pkgs)

        with self.patch_checker, self.patch_store, patch_configs:
            result_dict = main._get_pair_compatibility_dict(
                'package1')

        self.assertEqual(result_dict, expected)

    def test__get_pair_compatibility_dict_self_conflict(self):
        # If the pair package is not self compatible, the package being checked
        # should not be marked as CHECK_WARNING.
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }

        PACKAGE_1 = package.Package("package1")
        PACKAGE_2 = package.Package("tensorflow")
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
            'py2': { 'status': 'CHECK_WARNING', 'details': {} },
            'py3': { 'status': 'CHECK_WARNING', 'details': {} },
        }
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'main._get_self_compatibility_dict',
            mock_self_res)

        pkgs = ['tensorflow']
        patch_configs = mock.patch('main.configs.PKG_LIST', pkgs)

        with self.patch_checker, self.patch_store, patch_self_status, \
                patch_configs:
            result_dict = main._get_pair_compatibility_dict(
                'package1')

        self.assertEqual(result_dict, expected)

    def test__get_check_results_success(self):
        expected_self_res = {
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }
        expected_google_res = {
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }
        expected_dep_res = { 'status': 'UP_TO_DATE', 'details': {}, }

        mock_self_res = mock.Mock()
        mock_self_res.return_value = expected_self_res

        mock_google_res = mock.Mock()
        mock_google_res.return_value = expected_google_res

        mock_dep_res = mock.Mock()
        mock_dep_res.return_value = expected_dep_res

        patch_self_res = mock.patch(
            'main._get_self_compatibility_dict', mock_self_res)
        patch_google_res = mock.patch(
            'main._get_pair_compatibility_dict', mock_google_res)
        patch_dep_res = mock.patch(
            'main._get_dependency_dict', mock_dep_res)

        with patch_self_res, patch_google_res, patch_dep_res:
            self_res, google_res, dep_res = main._get_check_results('opencensus')
            status = main._get_badge_status(self_res, google_res, dep_res)

        self.assertEqual(self_res, expected_self_res)
        self.assertEqual(google_res, expected_google_res)
        self.assertEqual(dep_res, expected_dep_res)
        self.assertEqual(status, 'SUCCESS')

    def test__get_check_results_unknown(self):
        expected_self_res = {
            'py2': { 'status': 'UNKNOWN', 'details': {} },
            'py3': { 'status': 'UNKNOWN', 'details': {} },
        }
        expected_google_res = {
            'py2': { 'status': 'UNKNOWN', 'details': {} },
            'py3': { 'status': 'UNKNOWN', 'details': {} },
        }
        expected_dep_res = { 'status': 'UNKNOWN', 'details': {}, }

        mock_self_res = mock.Mock()
        mock_self_res.return_value = expected_self_res

        mock_google_res = mock.Mock()
        mock_google_res.return_value = expected_google_res

        mock_dep_res = mock.Mock()
        mock_dep_res.return_value = expected_dep_res

        patch_self_res = mock.patch(
            'main._get_self_compatibility_dict', mock_self_res)
        patch_google_res = mock.patch(
            'main._get_pair_compatibility_dict', mock_google_res)
        patch_dep_res = mock.patch(
            'main._get_dependency_dict', mock_dep_res)

        with patch_self_res, patch_google_res, patch_dep_res:
            self_res, google_res, dep_res = main._get_check_results('unknown_package')
            status = main._get_badge_status(self_res, google_res, dep_res)

        self.assertEqual(self_res, expected_self_res)
        self.assertEqual(google_res, expected_google_res)
        self.assertEqual(dep_res, expected_dep_res)
        self.assertEqual(status, 'UNKNOWN')

    def test__get_check_results_check_warning(self):
        expected_self_res = {
            'py2': { 'status': 'CHECK_WARNING', 'details': {} },
            'py3': { 'status': 'CHECK_WARNING', 'details': {} },
        }
        expected_google_res = {
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }
        expected_dep_res = { 'status': 'UP_TO_DATE', 'details': {}, }

        mock_self_res = mock.Mock()
        mock_self_res.return_value = expected_self_res

        mock_google_res = mock.Mock()
        mock_google_res.return_value = expected_google_res

        mock_dep_res = mock.Mock()
        mock_dep_res.return_value = expected_dep_res

        patch_self_res = mock.patch(
            'main._get_self_compatibility_dict', mock_self_res)
        patch_google_res = mock.patch(
            'main._get_pair_compatibility_dict', mock_google_res)
        patch_dep_res = mock.patch(
            'main._get_dependency_dict', mock_dep_res)

        with patch_self_res, patch_google_res, patch_dep_res:
            self_res, google_res, dep_res = main._get_check_results('opencensus')
            status = main._get_badge_status(self_res, google_res, dep_res)

        self.assertEqual(self_res, expected_self_res)
        self.assertEqual(google_res, expected_google_res)
        self.assertEqual(dep_res, expected_dep_res)
        self.assertEqual(status, 'CHECK_WARNING')
