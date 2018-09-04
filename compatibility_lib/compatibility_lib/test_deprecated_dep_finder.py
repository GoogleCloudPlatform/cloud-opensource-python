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

import unittest

import mock

from compatibility_lib import deprecated_dep_finder
from compatibility_lib import fake_compatibility_store


class TestDeprecatedDepFinder(unittest.TestCase):
    PKG_INFO = {
        'info': {
            'classifiers': [
                "Development Status :: 7 - Inactive",
                "Intended Audience :: Developers",
                "License :: OSI Approved:: Apache Software License",
                "Operating System :: POSIX",
                "Programming Language:: Python :: 2",
                "Programming Language:: Python :: 2.7",
                "Programming Language:: Python :: 3",
                "Programming Language:: Python :: 3.4",
                "Programming Language:: Python :: 3.5",
                "Topic :: Internet :: WWW / HTTP",
            ]
        }
    }

    def setUp(self):
        self.DEP_INFO = {
            'dep1': {
                'installed_version': '2.1.0',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '2.1.0',
                'current_time': '2018-08-27T17:04:57.260105',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': True,
            },
            'dep2': {
                'installed_version': '3.6.1',
                'installed_version_time': '2018-08-13T22:47:09',
                'latest_version': '3.6.1',
                'current_time': '2018-08-27T17:04:57.934866',
                'latest_version_time': '2018-08-13T22:47:09',
                'is_latest': True,
            },
        }

        self.SELF_COMP_RES = ((
            {
                'result': 'SUCCESS',
                'packages': ['package1'],
                'description': None,
                'dependency_info': self.DEP_INFO,
            },
        ),)
        self.mock_checker = mock.Mock(autospec=True)
        self.fake_store = fake_compatibility_store.CompatibilityStore()

        self.mock_checker.get_self_compatibility.return_value = \
            self.SELF_COMP_RES

        self.patch_checker = mock.patch(
            'compatibility_lib.deprecated_dep_finder.utils.checker',
            self.mock_checker)
        self.patch_store = mock.patch(
            'compatibility_lib.deprecated_dep_finder.utils.store',
            self.fake_store)

    def test_constructor_default(self):
        from compatibility_lib import utils

        with self.patch_checker, self.patch_store:
            finder = deprecated_dep_finder.DeprecatedDepFinder()

        self.assertEqual(finder.py_version, '3')
        self.assertTrue(
            isinstance(finder._dependency_info_getter, utils.DependencyInfo))

    def test_constructor_explicit(self):
        from compatibility_lib import utils

        with self.patch_checker, self.patch_store:
            finder = deprecated_dep_finder.DeprecatedDepFinder(py_version='2')

        self.assertEqual(finder.py_version, '2')
        self.assertIsInstance(
            finder._dependency_info_getter, utils.DependencyInfo)

    def test__get_development_status_from_pypi_error(self):
        PKG_INFO = {
            'test': {
                'test_key_error': [],
            }
        }

        mock_call_pypi_json_api = mock.Mock(autospec=True)
        mock_call_pypi_json_api.return_value = PKG_INFO

        patch_utils = mock.patch(
            'compatibility_lib.deprecated_dep_finder.utils.call_pypi_json_api',
            mock_call_pypi_json_api)

        with patch_utils, self.patch_checker, self.patch_store:
            finder = deprecated_dep_finder.DeprecatedDepFinder()
            development_status = finder._get_development_status_from_pypi(
                'package1')

        self.assertIsNone(development_status)

    def test__get_development_status_from_pypi(self):
        mock_call_pypi_json_api = mock.Mock(autospec=True)
        mock_call_pypi_json_api.return_value = self.PKG_INFO

        patch_utils = mock.patch(
            'compatibility_lib.deprecated_dep_finder.utils.call_pypi_json_api',
            mock_call_pypi_json_api)

        with patch_utils, self.patch_checker, self.patch_store:
            finder = deprecated_dep_finder.DeprecatedDepFinder()
            development_status = finder._get_development_status_from_pypi(
                'package1')

        expected_development_status = "Development Status :: 7 - Inactive"
        self.assertEqual(development_status, expected_development_status)

    def test_get_deprecated_deps(self):
        mock_call_pypi_json_api = mock.Mock(autospec=True)
        mock_call_pypi_json_api.return_value = self.PKG_INFO

        patch_utils = mock.patch(
            'compatibility_lib.deprecated_dep_finder.utils.call_pypi_json_api',
            mock_call_pypi_json_api)

        with patch_utils, self.patch_checker, self.patch_store:
            finder = deprecated_dep_finder.DeprecatedDepFinder()
            deprecated_deps = finder.get_deprecated_deps('opencensus')

        expected_deprecated_deps = ['dep1', 'dep2', 'dep3']
        self.assertEqual(set(deprecated_deps), set(expected_deprecated_deps))
