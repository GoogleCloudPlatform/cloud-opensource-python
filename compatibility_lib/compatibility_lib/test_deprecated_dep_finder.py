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
        self.mock_checker = mock.Mock()
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
        self.assertTrue(
            isinstance(finder._dependency_info_getter, utils.DependencyInfo))

    def test__get_development_status_from_pypi_error(self):
        pass

    def test__get_development_status_from_pypi(self):
        pass

    def test_get_deprecated_deps(self):
        pass
