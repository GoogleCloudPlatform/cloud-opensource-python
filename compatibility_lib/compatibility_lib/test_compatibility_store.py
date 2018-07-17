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

import mock

from compatibility_lib import compatibility_store
from compatibility_lib import package

PACKAGE_1 = package.Package("package1")
PACKAGE_2 = package.Package("package2")
PACKAGE_3 = package.Package("package3")
PACKAGE_4 = package.Package("package4")


class TestCompatibilityResult(unittest.TestCase):

    def test_constructor_default(self):
        packages = [PACKAGE_1, PACKAGE_2, PACKAGE_3, PACKAGE_4]
        python_major_version = 3
        status = compatibility_store.Status.SUCCESS

        compat_result = compatibility_store.CompatibilityResult(
            packages=packages,
            python_major_version=python_major_version,
            status=status)

        self.assertEqual(compat_result.packages, packages)
        self.assertEqual(
            compat_result.python_major_version, python_major_version)
        self.assertEqual(compat_result.status, status)
        self.assertIsNone(compat_result.details)
        self.assertIsNone(compat_result.dependency_info)

    def test_constructor_explicit(self):
        packages = [PACKAGE_1, PACKAGE_2, PACKAGE_3, PACKAGE_4]
        python_major_version = 3
        status = compatibility_store.Status.SUCCESS
        details = 'Could not find a version that satisfies the ' \
                  'requirement apache-beam[gcp]==2.4.0'
        dependency_info = {
            "cachetools": {
                "installed_version": "2.1.0",
                "installed_version_time": "2018-05-12T16:26:31",
                "latest_version": "2.1.0",
                "current_time": "2018-07-13T17:11:29.140608",
                "latest_version_time": "2018-05-12T16:26:31",
                "is_latest": True}}
        timestamp = datetime.datetime.utcnow()

        compat_result = compatibility_store.CompatibilityResult(
            packages=packages,
            python_major_version=python_major_version,
            status=status,
            details=details,
            dependency_info=dependency_info,
            timestamp=timestamp)

        self.assertEqual(compat_result.packages, packages)
        self.assertEqual(
            compat_result.python_major_version, python_major_version)
        self.assertEqual(compat_result.status, status)
        self.assertEqual(compat_result.details, details)
        self.assertEqual(compat_result.dependency_info, dependency_info)
        self.assertEqual(compat_result.timestamp, timestamp)


class TestCompatibilityStore(unittest.TestCase):

    def test_constructor(self):
        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        expected__self_table_id = 'compatibility_checker.self_compatibility_status'
        expected__pairwise_table_id = 'compatibility_checker.pairwise_compatibility_status'
        expected__release_time_table_id = 'compatibility_checker.release_time_for_dependencies'

        with patch_client:
            store = compatibility_store.CompatibilityStore()

        self.assertEqual(store._self_table_id, expected__self_table_id)
        self.assertEqual(store._pairwise_table_id, expected__pairwise_table_id)
        self.assertEqual(store._release_time_table_id, expected__release_time_table_id)

        self.assertEqual(
            store._self_table,
            compatibility_store._SELF_COMPATIBILITY_STATUS_TABLE_NAME)
        self.assertEqual(
            store._pairwise_table,
            compatibility_store._PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME)
        self.assertEqual(
            store._release_time_table,
            compatibility_store._RELEASE_TIME_FOR_DEPENDENCIES_TABLE_NAME)

    def test_get_packages(self):
        mock_client = mock.Mock()
        pkgs = ['google-api-core', 'apache-beam']
        mock_client.query.return_value = [
            [pkgs[0], 'SUCCESS'],
            [pkgs[1], 'CHECK WARNING'],
        ]
        def MockClient():
            return mock_client

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)
        with patch_client:
            store = compatibility_store.CompatibilityStore()
            packages = list(store.get_packages())

        self.assertEqual(len(packages), 2)

        for i, pkg in enumerate(packages):
            self.assertTrue(
                isinstance(pkg, compatibility_store.package.Package))
            self.assertEqual(pkg.install_name, pkgs[i])

    def test_get_self_compatibility(self):
        mock_client = mock.Mock()
        def MockClient():
            return mock_client

        row = mock.Mock(
            install_name=PACKAGE_1.install_name,
            status='SUCCESS',
            py_version='3',
            timestamp='2018-07-17 01:07:08.936648 UTC',
            details=None)

        mock_client.query.return_value = [row]
        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()

        patch_bigquery = mock.patch(
            'compatibility_lib.compatibility_store.bigquery', MockBigquery)

        with patch_bigquery:
            res = store.get_self_compatibility(PACKAGE_1)

        self.assertEqual(len(res), 1)
        self.assertTrue(
            isinstance(res[0], compatibility_store.CompatibilityResult))


    def test_get_self_compatibilities(self):
        mock_client = mock.Mock()

        def MockClient():
            return mock_client

        packages = [PACKAGE_1, PACKAGE_2, PACKAGE_3, PACKAGE_4]
        rows = []
        for pkg in packages:
            row = mock.Mock()
            row.install_name = pkg.install_name
            row.status = 'SUCCESS'
            row.py_version = '3'
            row.timestamp = '2018-07-17 01:07:08.936648 UTC'
            row.details = None
            rows.append(row)

        mock_client.query.return_value = rows

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()

        patch_bigquery = mock.patch(
            'compatibility_lib.compatibility_store.bigquery', MockBigquery)

        with patch_bigquery:
            res = store.get_self_compatibilities(packages)

        self.assertEqual(len(res), 4)
        self.assertEqual(frozenset(res.keys()), frozenset(packages))

    def test_get_pair_compatibility_value_error(self):
        mock_client = mock.Mock()

        def MockClient():
            return mock_client

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()

        packages = [PACKAGE_1]
        with self.assertRaises(ValueError):
            store.get_pair_compatibility(packages)

    def test_get_pair_compatibility(self):
        mock_client = mock.Mock()

        def MockClient():
            return mock_client

        row = mock.Mock(
            status='SUCCESS',
            py_version='3',
            timestamp='2018-07-17 02:14:27.15768 UTC',
            details=None)
        mock_client.query.return_value = [row]

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()

        patch_bigquery = mock.patch(
            'compatibility_lib.compatibility_store.bigquery', MockBigquery)
        packages = [PACKAGE_1, PACKAGE_2]

        with patch_bigquery:
            res = store.get_pair_compatibility(packages)

        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0].packages), 2)
        self.assertTrue(
            isinstance(res[0], compatibility_store.CompatibilityResult))

    def test_compatibility_combinations(self):
        mock_client = mock.Mock()

        def MockClient():
            return mock_client

        row1 = mock.Mock(
            install_name_lower='package1',
            install_name_higher='package2',
            status='SUCCESS',
            py_version='3',
            timestamp='2018-07-17 02:14:27.15768 UTC',
            details=None)
        row2 = mock.Mock(
            install_name_lower='package1',
            install_name_higher='package3',
            status='SUCCESS',
            py_version='3',
            timestamp='2018-07-17 02:14:27.15768 UTC',
            details=None)
        row3 = mock.Mock(
            install_name_lower='package2',
            install_name_higher='package3',
            status='SUCCESS',
            py_version='3',
            timestamp='2018-07-17 02:14:27.15768 UTC',
            details=None)
        mock_client.query.return_value = [row1, row2, row3]

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()

        patch_bigquery = mock.patch(
            'compatibility_lib.compatibility_store.bigquery', MockBigquery)
        packages = [PACKAGE_1, PACKAGE_2, PACKAGE_3]

        with patch_bigquery:
            res = store.get_compatibility_combinations(packages)

        expected_pair_1 = frozenset({PACKAGE_1, PACKAGE_2})
        expected_pair_2 = frozenset({PACKAGE_1, PACKAGE_3})
        expected_pair_3 = frozenset({PACKAGE_2, PACKAGE_3})

        self.assertEqual(len(res.keys()), 3)
        self.assertEqual(
            frozenset(res.keys()),
            frozenset({expected_pair_1, expected_pair_2, expected_pair_3}))

    def test_save_compatibility_statuses_pair(self):
        mock_client = mock.Mock()
        packages = [PACKAGE_1, PACKAGE_2]
        timestamp = '2018-07-17 03:01:06.11693 UTC'
        status = compatibility_store.Status.SUCCESS
        comp_status = mock.Mock(
            packages=packages,
            python_major_version='3',
            status=status,
            details=None,
            dependency_info=None,
            timestamp=timestamp)
        row_pairwise = {
            'install_name_lower': 'package1',
            'install_name_higher': 'package2',
            'status': 'SUCCESS',
            'py_version': '3',
            'timestamp': timestamp,
            'details': None,
        }

        def MockClient():
            return mock_client

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses([comp_status])

        mock_client.insert_rows.assert_called_with(
            store._pairwise_table, [row_pairwise])

    def test_save_compatibility_statuses_self(self):
        mock_client = mock.Mock()
        packages = [PACKAGE_1]
        timestamp = '2018-07-17 03:01:06.11693 UTC'
        status = compatibility_store.Status.SUCCESS
        comp_status = mock.Mock(
            packages=packages,
            python_major_version='3',
            status=status,
            details=None,
            dependency_info=None,
            timestamp=timestamp)
        row_self = {
            'install_name': 'package1',
            'status': 'SUCCESS',
            'py_version': '3',
            'timestamp': timestamp,
            'details': None,
        }

        def MockClient():
            return mock_client

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses([comp_status])

        mock_client.insert_rows.assert_called_with(
            store._self_table, [row_self])

    def test_save_compatibility_statuses_release_time(self):
        mock_client = mock.Mock()
        packages = [PACKAGE_1]
        timestamp = '2018-07-17 03:01:06.11693 UTC'
        status = compatibility_store.Status.SUCCESS
        comp_status = mock.Mock(
            packages=packages,
            python_major_version='3',
            status=status,
            details=None,
            dependency_info={'dep1': {
                'installed_version': '2.1.0',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '2.1.0',
                'current_time': '2018-07-13T17:11:29.140608',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': True,
            }},
            timestamp=timestamp)
        row_release_time = {
            'install_name': 'package1',
            'dep_name': 'dep1',
            'installed_version': '2.1.0',
            'installed_version_time': '2018-05-12T16:26:31',
            'latest_version': '2.1.0',
            'timestamp': '2018-07-13T17:11:29.140608',
            'latest_version_time': '2018-05-12T16:26:31',
            'is_latest': True,
        }

        def MockClient():
            return mock_client

        patch_client = mock.patch(
            'compatibility_lib.compatibility_store.bigquery.Client',
            MockClient)

        with patch_client:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses([comp_status])

        mock_client.insert_rows.assert_called_with(
            store._release_time_table, [row_release_time])


class MockClient(object):
    def dataset(self, dataset_name):
        dataset_ref = mock.Mock()

        def table(table_name):
            return table_name

        dataset_ref.table = table

        return dataset_ref

    def get_table(self, table_name):
        return table_name


class MockBigquery(object):
    @staticmethod
    def ArrayQueryParameter(name, array_type, values):
        return [name, array_type, values]

    @staticmethod
    def ScalarQueryParameter(name, array_type, values):
        return [name, array_type, values]

    @staticmethod
    def QueryJobConfig():
        return mock.Mock()
