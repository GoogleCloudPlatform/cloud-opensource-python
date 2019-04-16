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
PACKAGE_4 = package.Package("package4[gcp]")


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

    def test_with_updated_dependency_info_new_dependencies(self):
        original_result = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1],
            python_major_version=3,
            status=compatibility_store.Status.SUCCESS,
            details="No details",
            dependency_info={'package1': {'installed_version': '1.2.3'}})
        updated_result = original_result.with_updated_dependency_info(
            {'package2': {'installed_version': '4.5.6'}})

        self.assertEqual(updated_result.dependency_info,
                         {
                             'package1': {'installed_version': '1.2.3'},
                             'package2': {'installed_version': '4.5.6'},
                         })

        # Test that non-dependency properties are unchanged.
        self.assertEqual(original_result.packages, updated_result.packages)
        self.assertEqual(original_result.python_major_version,
                         updated_result.python_major_version)
        self.assertEqual(original_result.status, updated_result.status)
        self.assertEqual(original_result.details, updated_result.details)
        self.assertEqual(original_result.timestamp, updated_result.timestamp)


    def test_with_updated_dependency_info_changed_dependencies(self):
        original_result = compatibility_store.CompatibilityResult(
            packages=[PACKAGE_1],
            python_major_version=3,
            status=compatibility_store.Status.SUCCESS,
            details="No details",
            dependency_info={'package1': {'installed_version': '1.2.3'}})
        updated_result = original_result.with_updated_dependency_info(
            {'package1': {'installed_version': '2.3.4'},
             'package2': {'installed_version': '4.5.6'}})

        self.assertEqual(updated_result.dependency_info,
                         {
                             'package1': {'installed_version': '2.3.4'},
                             'package2': {'installed_version': '4.5.6'},
                         })

        # Test that non-dependency properties are unchanged.
        self.assertEqual(original_result.packages, updated_result.packages)
        self.assertEqual(original_result.python_major_version,
                         updated_result.python_major_version)
        self.assertEqual(original_result.status, updated_result.status)
        self.assertEqual(original_result.details, updated_result.details)
        self.assertEqual(original_result.timestamp, updated_result.timestamp)


class TestCompatibilityStore(unittest.TestCase):

    def test_get_packages(self):
        pkgs = ['google-api-core', 'apache-beam']
        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            [pkgs[0], 'SUCCESS'],
            [pkgs[1], 'CHECK WARNING']]
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)

        with patch_pymysql:
            store = compatibility_store.CompatibilityStore()
            packages = list(store.get_packages())

        self.assertEqual(len(packages), 2)

        for i, pkg in enumerate(packages):
            self.assertTrue(
                isinstance(pkg, compatibility_store.package.Package))
            self.assertEqual(pkg.install_name, pkgs[i])

    def test_get_self_compatibility(self):
        row = (PACKAGE_1.install_name, 'SUCCESS', '3',
               '2018-07-17 01:07:08.936648 UTC', None)

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [row]
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql',
            mock_pymysql)

        store = compatibility_store.CompatibilityStore()
        with patch_pymysql:
            res = store.get_self_compatibility(PACKAGE_1)

        self.assertEqual(len(res), 1)
        self.assertTrue(
            isinstance(res[0], compatibility_store.CompatibilityResult))

    def test_get_self_compatibilities(self):
        packages = [PACKAGE_1, PACKAGE_2, PACKAGE_3, PACKAGE_4]
        rows = []
        for pkg in packages:
            row = (pkg.install_name, 'SUCCESS', '3',
                   '2018-07-17 01:07:08.936648 UTC', None)
            rows.append(row)

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = rows
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql',
            mock_pymysql)
        store = compatibility_store.CompatibilityStore()

        with patch_pymysql:
            res = store.get_self_compatibilities(packages)

        self.assertEqual(len(res), 4)
        self.assertEqual(frozenset(res.keys()), frozenset(packages))

    def test_get_pair_compatibility_value_error(self):
        # get_pair_compatibility needs 2 packages to run the check, or it will
        # raise ValueError.
        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        store = compatibility_store.CompatibilityStore()

        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql',
            mock_pymysql)
        packages = [PACKAGE_1]
        with patch_pymysql, self.assertRaises(ValueError):
            store.get_pair_compatibility(packages)

    def test_get_pair_compatibility(self):
        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        row = ('pkg1', 'pkg2', 'SUCCESS', '3',
               '2018-07-17 02:14:27.15768 UTC', None)
        mock_cursor.fetchall.return_value = [row]
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql',
            mock_pymysql)
        store = compatibility_store.CompatibilityStore()
        packages = [PACKAGE_1, PACKAGE_2]

        with patch_pymysql:
            res = store.get_pair_compatibility(packages)

        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0].packages), 2)
        self.assertTrue(
            isinstance(res[0], compatibility_store.CompatibilityResult))

    def test_compatibility_combinations(self):
        row1 = ('package1', 'package2', 'SUCCESS',
                '3', '2018-07-17 02:14:27.15768 UTC', None)
        row2 = ('package1', 'package3', 'SUCCESS',
                '3', '2018-07-17 02:14:27.15768 UTC', None)
        row3 = ('package2', 'package3', 'SUCCESS',
                '3', '2018-07-17 02:14:27.15768 UTC', None)
        store = compatibility_store.CompatibilityStore()

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [row1, row2, row3]

        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)
        packages = [PACKAGE_1, PACKAGE_2, PACKAGE_3]

        with patch_pymysql:
            res = store.get_compatibility_combinations(packages)

        expected_pair_1 = frozenset({PACKAGE_1, PACKAGE_2})
        expected_pair_2 = frozenset({PACKAGE_1, PACKAGE_3})
        expected_pair_3 = frozenset({PACKAGE_2, PACKAGE_3})

        self.assertEqual(len(res.keys()), 3)
        self.assertEqual(
            frozenset(res.keys()),
            frozenset({expected_pair_1, expected_pair_2, expected_pair_3}))

    def test_save_compatibility_statuses_pair(self):
        packages = [PACKAGE_1, PACKAGE_2]
        status = compatibility_store.Status.SUCCESS
        comp_status = compatibility_store.CompatibilityResult(
            packages=packages,
            python_major_version='3',
            status=status,
            details=None,
            dependency_info=None,
            timestamp=None)
        row_pairwise = ('package1', 'package2', 'SUCCESS',
                        '3', None, None)

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)

        pair_sql = 'REPLACE INTO pairwise_compatibility_status values ' \
                    '(%s, %s, %s, %s, %s, %s)'

        with patch_pymysql:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses([comp_status])

        mock_cursor.executemany.assert_called_with(
            pair_sql, [row_pairwise])

    def test_save_compatibility_statuses_self(self):
        packages = [PACKAGE_1]
        status = compatibility_store.Status.SUCCESS
        comp_status = compatibility_store.CompatibilityResult(
            packages=packages,
            python_major_version='3',
            status=status,
            details=None,
            dependency_info=None,
            timestamp=None)
        row_self = ('package1', 'SUCCESS', '3', None, None)

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)

        self_sql = 'REPLACE INTO self_compatibility_status values ' \
                    '(%s, %s, %s, %s, %s)'

        with patch_pymysql:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses([comp_status])

        mock_cursor.executemany.assert_called_with(
            self_sql, [row_self])

    def test_save_compatibility_statuses_release_time(self):
        packages = [PACKAGE_1]
        status = compatibility_store.Status.SUCCESS
        comp_status = compatibility_store.CompatibilityResult(
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
            timestamp=None)
        row_release_time = ('package1', 'dep1', '2.1.0', '2018-05-12T16:26:31',
                            '2.1.0', '2018-05-12T16:26:31', True,
                            '2018-07-13T17:11:29.140608')

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)

        sql = 'REPLACE INTO release_time_for_dependencies values ' \
              '(%s, %s, %s, %s, %s, %s, %s, %s)'

        with patch_pymysql:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses([comp_status])

        mock_cursor.executemany.assert_called_with(
            sql, [row_release_time])

    def test_save_compatibility_statuses_release_time_for_latest(self):
        packages = [PACKAGE_4]
        timestamp = '2018-07-17 03:01:06.11693 UTC'
        status = compatibility_store.Status.SUCCESS
        comp_status_py2 = compatibility_store.CompatibilityResult(
            packages=packages,
            python_major_version='2',
            status=status,
            details=None,
            dependency_info={'package4': {
                'installed_version': '12.7.0',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '12.7.0',
                'current_time': '2018-07-13T17:11:29.140608',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': True,
            }},
            timestamp=timestamp)
        comp_status_py3 = compatibility_store.CompatibilityResult(
            packages=packages,
            python_major_version='3',
            status=status,
            details=None,
            dependency_info={'package4': {
                'installed_version': '2.2.0',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '2.7.0',
                'current_time': '2018-07-13T17:11:29.140608',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': False,
            }},
            timestamp=timestamp)
        row_release_time = ('package4[gcp]', 'package4', '12.7.0',
                            '2018-05-12T16:26:31', '12.7.0',
                            '2018-05-12T16:26:31', True,
                            '2018-07-13T17:11:29.140608')

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)
        sql = 'REPLACE INTO release_time_for_dependencies values ' \
              '(%s, %s, %s, %s, %s, %s, %s, %s)'

        with patch_pymysql:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses(
                [comp_status_py2, comp_status_py3])

        mock_cursor.executemany.assert_called_with(
            sql, [row_release_time])

    def test_save_compatibility_statuses_release_time_for_latest_many_packages(
            self):
        status = compatibility_store.Status.SUCCESS
        apache_beam_py2 = compatibility_store.CompatibilityResult(
            packages=[package.Package('apache-beam[gcp]')],
            python_major_version='2',
            status=status,
            details=None,
            dependency_info={
                'six': {
                    'installed_version': '9.9.9',
                    'installed_version_time': '2018-05-12T16:26:31',
                    'latest_version': '2.7.0',
                    'current_time': '2018-07-13T17:11:29.140608',
                    'latest_version_time': '2018-05-12T16:26:31',
                    'is_latest': False,
                }        ,
                'apache-beam': {
                'installed_version': '2.7.0',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '2.7.0',
                'current_time': '2018-07-13T17:11:29.140608',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': True,
            }},
            timestamp=None)
        apache_beam_py3 = compatibility_store.CompatibilityResult(
            packages=[package.Package('apache-beam[gcp]')],
            python_major_version='3',
            status=status,
            details=None,
            dependency_info={'apache-beam': {
                'installed_version': '2.2.0',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '2.7.0',
                'current_time': '2018-07-13T17:11:29.140608',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': False,
            }},
            timestamp=None)
        google_api_core_py2 = compatibility_store.CompatibilityResult(
            packages=[package.Package('google-api-core')],
            python_major_version='2',
            status=status,
            details=None,
            dependency_info={
                'google-api-core': {
                    'installed_version': '3.7.0',
                    'installed_version_time': '2018-05-12T16:26:31',
                    'latest_version': '2.7.0',
                    'current_time': '2018-07-13T17:11:29.140608',
                    'latest_version_time': '2018-05-12T16:26:31',
                    'is_latest': True,
                }},
            timestamp=None)
        google_api_core_py3 = compatibility_store.CompatibilityResult(
            packages=[package.Package('google-api-core')],
            python_major_version='3',
            status=status,
            details=None,
            dependency_info={'google-api-core': {
                'installed_version': '3.7.1',
                'installed_version_time': '2018-05-12T16:26:31',
                'latest_version': '2.7.0',
                'current_time': '2018-07-13T17:11:29.140608',
                'latest_version_time': '2018-05-12T16:26:31',
                'is_latest': False,
            }},
            timestamp=None)

        apache_beam_row = ('apache-beam[gcp]', 'apache-beam', '2.7.0',
                           '2018-05-12T16:26:31', '2.7.0',
                           '2018-05-12T16:26:31', True,
                           '2018-07-13T17:11:29.140608')

        six_row = ('apache-beam[gcp]', 'six', '9.9.9', '2018-05-12T16:26:31',
                   '2.7.0', '2018-05-12T16:26:31', False,
                   '2018-07-13T17:11:29.140608')

        google_api_core_row = ('google-api-core', 'google-api-core', '3.7.1',
                               '2018-05-12T16:26:31', '2.7.0',
                               '2018-05-12T16:26:31', False,
                               '2018-07-13T17:11:29.140608')

        mock_pymysql = mock.Mock()
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        patch_pymysql = mock.patch(
            'compatibility_lib.compatibility_store.pymysql', mock_pymysql)
        sql = 'REPLACE INTO release_time_for_dependencies values ' \
              '(%s, %s, %s, %s, %s, %s, %s, %s)'

        with patch_pymysql:
            store = compatibility_store.CompatibilityStore()
            store.save_compatibility_statuses(
                [apache_beam_py2,
                 apache_beam_py3,
                 google_api_core_py2,
                 google_api_core_py3])

        mock_cursor.executemany.assert_called_with(
            sql, [apache_beam_row, six_row, google_api_core_row])


class MockClient(object):

    def __init__(self, project=None):
        self.project = project

    def dataset(self, dataset_name):
        dataset_ref = mock.Mock()

        def table(table_name):
            return table_name

        dataset_ref.table = table

        return dataset_ref

    def get_table(self, table_name):
        return table_name
