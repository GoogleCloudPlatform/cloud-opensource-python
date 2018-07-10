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

import compatibility_lib


class TestGetCompatibilityData(unittest.TestCase):
    results = (
        [
            {
                'result': 'SUCCESS',
                'packages': ['google-api-core'],
                'description': None,
                'dependency_info': {
                    'cachetools': {
                        'installed_version': '2.1.0',
                        'latest_version': '2.1.0',
                        'current_time': '2018-07-10T11:02:40.481246',
                        'latest_version_time': '2018-05-12T16:26:31',
                        'is_latest': True
                    },
                    'certifi': {
                        'installed_version': '2018.4.16',
                        'latest_version': '2018.4.16',
                        'current_time': '2018-07-10T11:02:40.544879',
                        'latest_version_time': '2018-04-16T18:50:10',
                        'is_latest': True
                    },
                }
            }
        ],
    )

    def setUp(self):
        from compatibility_lib import compatibility_store

        self.mock_checker = mock.Mock()
        self.mock_checker.get_self_compatibility.return_value = self.results
        self.mock_checker.get_pairwise_compatibility.return_value = self.results

        self.mock_store = mock.Mock()
        self.mock_store.save_compatibility_statuses.return_value = None

        def mock_init():
            return None

        self.patch_constructor = mock.patch.object(
            compatibility_store.CompatibilityStore,
            '__init__',
            side_effect=mock_init)
        self.patch_checker = mock.patch(
            'compatibility_lib.get_compatibility_data.checker',
            self.mock_checker)
        self.patch_store = mock.patch(
            'compatibility_lib.get_compatibility_data.store',
            self.mock_store)

    def test__result_dict_to_compatibility_result(self):
        with self.patch_constructor, self.patch_checker, self.patch_store:
            from compatibility_lib import compatibility_store
            from compatibility_lib import get_compatibility_data

            python_version = 3
            res_list = get_compatibility_data._result_dict_to_compatibility_result(
                self.results, python_version)

        self.assertTrue(isinstance(
            res_list[0], compatibility_store.CompatibilityResult))

    def test_write_to_status_table(self):

        with self.patch_checker, self.patch_store:
            from compatibility_lib import get_compatibility_data

            get_compatibility_data.write_to_status_table()

        self.assertTrue(self.mock_checker.get_self_compatibility.called)
        self.assertTrue(self.mock_checker.get_pairwise_compatibility.called)
        self.assertTrue(self.mock_store.save_compatibility_statuses.called)
