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

    def test__get_missing_details_missing_inputs(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package
        TENSORFLOW = 'tensorflow'
        TENSORFLOW_RESULT_PY2 = compatibility_store.CompatibilityResult(
            packages=[package.Package(TENSORFLOW)],
            python_major_version=2,
            status=compatibility_store.Status.SUCCESS)
        TENSORFLOW_RESULT_PY3 = compatibility_store.CompatibilityResult(
            packages=[package.Package(TENSORFLOW)],
            python_major_version=3,
            status=compatibility_store.Status.SUCCESS)

        with self.assertRaises(ValueError):
            package_names = []
            results = []
            main._get_missing_details(package_names, results)

        with self.assertRaises(ValueError):
            package_names = []
            results = [TENSORFLOW_RESULT_PY2]
            main._get_missing_details(package_names, results)

        with self.assertRaises(ValueError):
            package_names = []
            results = [TENSORFLOW_RESULT_PY2, TENSORFLOW_RESULT_PY3]
            main._get_missing_details(package_names, results)

    def test__get_missing_details_too_many_inputs(self):
        from compatibility_lib import compatibility_store
        with self.assertRaises(ValueError):
            package_names = ['tensorflow', 'opencensus', 'compatibility-lib']
            results = []
            main._get_missing_details(package_names, results)

    def test__get_missing_details_unsupported_packages(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package
        TENSORFLOW = 'tensorflow'
        UNSUPPORTED = 'unsupported'
        UNSUPPORTED_RESULT_PY2 = compatibility_store.CompatibilityResult(
            packages=[package.Package(UNSUPPORTED)],
            python_major_version=2,
            status=compatibility_store.Status.UNKNOWN)
        PAIR_RESULT_PY3 = compatibility_store.CompatibilityResult(
            packages=[package.Package(p) for p in (TENSORFLOW, UNSUPPORTED)],
            python_major_version=3,
            status=compatibility_store.Status.UNKNOWN)

        with self.assertRaises(ValueError):
            package_names = [UNSUPPORTED]
            results = [UNSUPPORTED_RESULT_PY2]
            main._get_missing_details(package_names, results)

        with self.assertRaises(ValueError):
            package_names = [TENSORFLOW, UNSUPPORTED]
            results = [PAIR_RESULT_PY3]
            main._get_missing_details(package_names, results)

    def test__get_missing_details_for_self_compatibility(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import configs
        from compatibility_lib import package
        for package_name in configs.WHITELIST_PKGS:
            results = []
            if package_name not in ('tensorflow'):
                results.append(compatibility_store.CompatibilityResult(
                    packages=[package.Package(p) for p in package_name],
                    python_major_version=2,
                    status=compatibility_store.Status.SUCCESS))
            if package_name not in ('apache-beam[gcp]', 'gsutil'):
                results.append(compatibility_store.CompatibilityResult(
                    packages=[package.Package(p) for p in package_name],
                    python_major_version=3,
                    status=compatibility_store.Status.SUCCESS))
            details = main._get_missing_details([package_name], results)
            self.assertEqual(details, None)

    def test__get_missing_details_for_pair_compatibility(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import configs
        from compatibility_lib import package
        import itertools
        for p1, p2 in itertools.combinations(configs.WHITELIST_PKGS, r=2):
            pkgs = [p1, p2]
            results = []
            if all([p not in ('tensorflow') for p in pkgs]):
                results.append(compatibility_store.CompatibilityResult(
                    packages=[package.Package(p) for p in pkgs],
                    python_major_version=2,
                    status=compatibility_store.Status.SUCCESS))
            if all([p not in ('apache-beam[gcp]', 'gsutil') for p in pkgs]):
                results.append(compatibility_store.CompatibilityResult(
                    packages=[package.Package(p) for p in pkgs],
                    python_major_version=3,
                    status=compatibility_store.Status.SUCCESS))
            details = main._get_missing_details(pkgs, results)
            self.assertEqual(details, None)

    def test__get_missing_details_self_fail(self):
        from compatibility_lib import compatibility_store
        expected = {
            'opencensus': 'Missing data for python version(s): 2 and 3',
            'apache-beam[gcp]': 'Missing data for python version(s): 2',
            'tensorflow': 'Missing data for python version(s): 3',}

        for name, expected_details in expected.items():
            package_names = [name]
            results = []
            details = main._get_missing_details(package_names, results)
            self.assertEqual(details, expected_details)

    def test__get_missing_details_pair_fail(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package
        package_names = ['opencensus', 'compatibility-lib']
        results = [compatibility_store.CompatibilityResult(
            packages=[package.Package(name) for name in package_names],
            python_major_version=2,
            status=compatibility_store.Status.SUCCESS)]
        details = main._get_missing_details(package_names, results)
        expected_details = 'Missing data for python version(s): 3'
        self.assertEqual(details, expected_details)

    def test__get_self_compatibility_dict(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': {'status': main.BadgeStatus.SUCCESS, 'details':
                    'The package does not support this version of python.'},
            'py3': {'status': main.BadgeStatus.SUCCESS, 'details': 'NO DETAILS'},
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
        success_status = main.BadgeStatus.SUCCESS
        expected = {
            'py2': {'status': main.BadgeStatus.SUCCESS,
                    'details': 'The package does not support this version of python.'},
            'py3': {'status': main.BadgeStatus.SUCCESS,
                    'details': 'The package does not support this version of python.'}
        }

        pkgs = ['tensorflow', 'apache-beam[gcp]']
        patch_configs = mock.patch('main.configs.PKG_LIST', pkgs)
        with self.patch_checker, self.patch_store, patch_configs:
            result_dict = main._get_pair_compatibility_dict('tensorflow')

        self.assertEqual(result_dict, expected)

    def test__get_pair_compatibility_dict_internal_error(self):
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': {'status': main.BadgeStatus.PAIR_INCOMPATIBLE,
                    'details': {'package2': 'NO DETAILS'} },
            'py3': {'status': main.BadgeStatus.PAIR_INCOMPATIBLE,
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
            'py2': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
            'py3': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
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

    def test__get_pair_compatibility_dict_internal_error(self):
        expected_self = {
            'py2': {'status': main.BadgeStatus.INTERNAL_ERROR,
                    'details': 'NO DETAILS'},
            'py3': {'status': main.BadgeStatus.INTERNAL_ERROR,
                    'details': 'NO DETAILS'}
        }
        expected_google = {
            'py2': {'status': main.BadgeStatus.INTERNAL_ERROR,
                    'details': 'NO DETAILS'},
            'py3': {'status': main.BadgeStatus.INTERNAL_ERROR,
                    'details': 'NO DETAILS'}
        }
        expected_dep = {
            'status': main.BadgeStatus.INTERNAL_ERROR,
            'details': 'NO DETAILS'
        }

        test = mock.Mock(side_effect=Exception())
        patch_get_self = mock.patch('main._get_self_compatibility_dict', test)
        with patch_get_self:
            results = main._get_check_results('tensorflow')

        self_res, google_res, dep_res = results
        self.assertEqual(self_res, expected_self)
        self.assertEqual(google_res, expected_google)
        self.assertEqual(dep_res, expected_dep)

    def test__get_pair_compatibility_dict_self_conflict(self):
        # If the pair package is not self compatible, the package being checked
        # should not be marked as `INTERNAL_ERROR`.
        from compatibility_lib import compatibility_store
        from compatibility_lib import package

        expected = {
            'py2': {'status': main.BadgeStatus.SUCCESS,
                    'details': 'The package does not support this version of python.'},
            'py3': {'status': main.BadgeStatus.SUCCESS, 'details': {}},
        }

        PACKAGE_1 = package.Package("opencensus")
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
            'py2': { 'status': main.BadgeStatus.SELF_INCOMPATIBLE, 'details': {} },
            'py3': { 'status': main.BadgeStatus.SELF_INCOMPATIBLE, 'details': {} },
        }
        mock_self_res.return_value = self_res
        patch_self_status = mock.patch(
            'main._get_self_compatibility_dict',
            mock_self_res)

        pkgs = [p.install_name for p in (PACKAGE_1, PACKAGE_2)]
        patch_configs = mock.patch('main.configs.PKG_LIST', pkgs)

        with self.patch_checker, self.patch_store, patch_self_status, \
                patch_configs:
            result_dict = main._get_pair_compatibility_dict(
                PACKAGE_1.install_name)

        self.assertEqual(result_dict, expected)

    def test__get_check_results_success(self):
        expected_self_res = {
            'py2': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
            'py3': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
        }
        expected_google_res = {
            'py2': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
            'py3': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
        }
        expected_dep_res = { 'status': main.BadgeStatus.SUCCESS, 'details': {}, }

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
        self.assertEqual(status, main.BadgeStatus.SUCCESS)

    def test__get_check_results_unknown(self):
        expected_self_res = {
            'py2': { 'status': main.BadgeStatus.UNKNOWN_PACKAGE, 'details': {} },
            'py3': { 'status': main.BadgeStatus.UNKNOWN_PACKAGE, 'details': {} },
        }
        expected_google_res = {
            'py2': { 'status': main.BadgeStatus.UNKNOWN_PACKAGE, 'details': {} },
            'py3': { 'status': main.BadgeStatus.UNKNOWN_PACKAGE, 'details': {} },
        }
        expected_dep_res = { 'status': main.BadgeStatus.UNKNOWN_PACKAGE, 'details': {}, }

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
        self.assertEqual(status, main.BadgeStatus.UNKNOWN_PACKAGE)

    def test__get_check_results_internal_error(self):
        expected_self_res = {
            'py2': { 'status': main.BadgeStatus.INTERNAL_ERROR, 'details': {} },
            'py3': { 'status': main.BadgeStatus.INTERNAL_ERROR, 'details': {} },
        }
        expected_google_res = {
            'py2': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
            'py3': { 'status': main.BadgeStatus.SUCCESS, 'details': {} },
        }
        expected_dep_res = { 'status': main.BadgeStatus.SUCCESS, 'details': {}, }

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
        self.assertEqual(status, main.BadgeStatus.INTERNAL_ERROR)
