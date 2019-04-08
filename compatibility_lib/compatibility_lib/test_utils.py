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

UNKNOWN_STATUS_RESULT = {
    'result': 'UNKNOWN',
}

DEP_INFO = {
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


class MockChecker(object):
    def check(self, packages, python_version):
        if not utils._is_package_in_whitelist(packages):
            UNKNOWN_STATUS_RESULT['packages'] = packages
            UNKNOWN_STATUS_RESULT['description'] = 'Package is not supported' \
                                                   ' by our checker server.'
            return UNKNOWN_STATUS_RESULT

        return {
            'result': 'SUCCESS',
            'packages': packages,
            'description': None,
            'dependency_info': DEP_INFO,
        }

    def get_compatibility(self, python_version, packages=None):
        return [[self.check(
            packages=packages, python_version=python_version)]]


class TestDependencyInfo(unittest.TestCase):

    def setUp(self):
        self.mock_checker = MockChecker()
        self.fake_store = fake_compatibility_store.CompatibilityStore()

    def test_constructor_default(self):
        dep_info_getter = utils.DependencyInfo(
            checker=self.mock_checker, store=self.fake_store)

        self.assertEqual(dep_info_getter.py_version, '3')

    def test_constructor_explicit(self):
        dep_info_getter = utils.DependencyInfo(
            py_version='2', checker=self.mock_checker, store=self.fake_store)

        self.assertEqual(dep_info_getter.py_version, '2')

    def test__get_from_cloud_sql_exists(self):
        dep_info_getter = utils.DependencyInfo(
            checker=self.mock_checker, store=self.fake_store)
        dep_info = dep_info_getter._get_from_cloud_sql('opencensus')

        self.assertIsNotNone(dep_info)

    def test__get_from_cloud_sql_not_exists(self):
        dep_info_getter = utils.DependencyInfo(
            checker=self.mock_checker, store=self.fake_store)
        dep_info = dep_info_getter._get_from_cloud_sql('pkg_not_in_config')

        self.assertIsNone(dep_info)

    def test__get_from_endpoint(self):
        dep_info_getter = utils.DependencyInfo(
            checker=self.mock_checker, store=self.fake_store)
        dep_info = dep_info_getter._get_from_endpoint('opencensus')

        self.assertEqual(dep_info, DEP_INFO)

    def test__get_from_endpoint_raise_exception(self):
        dep_info_getter = utils.DependencyInfo(
            checker=self.mock_checker, store=self.fake_store)

        with self.assertRaises(utils.PackageNotSupportedError):
            dep_info_getter._get_from_endpoint('pkg_not_in_config')

    def test_get_dependency_info_compatibility_store(self):
        self.fake_store.save_compatibility_statuses(
            compatibility_store
        )
        dep_info_getter = utils.DependencyInfo(
            checker=self.mock_checker, store=self.fake_store)
        dep_info = dep_info_getter.get_dependency_info('opencensus')

        self.assertIsNotNone(dep_info)


class Test__parse_datetime(unittest.TestCase):

  def test__parse_datetime(self):
      date_string = '2018-08-16T15:42:04.351677'
      expected = '2018-08-16 00:00:00'
      res = utils._parse_datetime(date_string)
      self.assertEqual(str(res), expected)

  def test__parse_datetime_empty(self):
      res = utils._parse_datetime(None)
      self.assertIsNone(res)
