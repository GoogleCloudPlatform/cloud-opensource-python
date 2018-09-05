# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import unittest

from compatibility_lib import fake_compatibility_store
from compatibility_lib import utils


class TestDependencyInfo(unittest.TestCase):

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
            'compatibility_lib.utils.checker',
            self.mock_checker)
        self.patch_store = mock.patch(
            'compatibility_lib.utils.store',
            self.fake_store)

    def test_constructor_default(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo()

        self.assertEqual(dep_info_getter.py_version, '3')

    def test_constructor_explicit(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo(py_version='2')

        self.assertEqual(dep_info_getter.py_version, '2')

    def test__get_from_bigquery_exists(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo()
            dep_info = dep_info_getter._get_from_bigquery('opencensus')

        self.assertIsNotNone(dep_info)

    def test__get_from_bigquery_not_exists(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo()
            dep_info = dep_info_getter._get_from_bigquery('pkg_not_in_config')

        self.assertIsNone(dep_info)

    def test__get_from_endpoint(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo()
            dep_info = dep_info_getter._get_from_endpoint('package1')

        self.assertEqual(dep_info, self.DEP_INFO)

    def test_get_dependency_info_bigquery(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo()
            dep_info = dep_info_getter.get_dependency_info('opencensus')

        self.assertIsNotNone(dep_info)

    def test_get_dependency_info_endpoint(self):
        with self.patch_checker, self.patch_store:
            dep_info_getter = utils.DependencyInfo()
            dep_info = dep_info_getter.get_dependency_info('package1')

        self.assertEqual(dep_info, self.DEP_INFO)


class Test__parse_datetime(unittest.TestCase):

  def test__parse_datetime(self):
    date_string = '2018-08-16T15:42:04.351677'
    expected = '2018-08-16 00:00:00'
    res = utils._parse_datetime(date_string)
    self.assertEqual(str(res), expected)
