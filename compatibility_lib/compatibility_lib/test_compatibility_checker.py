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

from compatibility_lib import compatibility_checker


class TestCompatibilityChecker(unittest.TestCase):

    def test_check(self):
        import json

        checker = compatibility_checker.CompatibilityChecker()

        packages = 'test_pkg'
        python_version = 3

        data = {
            'python-version': python_version,
            'packages': packages
        }

        request = mock.Mock()

        mock_request = mock.Mock()
        mock_request.Request.return_value = request

        urlopen_res = mock.Mock()
        mock_request.urlopen.return_value = urlopen_res
        json_mock = mock.Mock()
        json_mock.read.return_value = b'{}'
        urlopen_res.__enter__ = mock.Mock(return_value=json_mock)
        urlopen_res.__exit__ = mock.Mock(return_value=None)

        patch_request = mock.patch(
            'compatibility_lib.compatibility_checker.urllib.request',
            mock_request)

        with patch_request:
            checker.check(packages, python_version)

        mock_request.Request.assert_called_with(
            compatibility_checker.SERVER_URL, json.dumps(data).encode('utf-8'))
        mock_request.urlopen.assert_called_with(request)

    def test_get_self_compatibility(self):
        import itertools

        checker = compatibility_checker.CompatibilityChecker()

        pkg_list = ['pkg1', 'pkg2']
        python_version = 3
        pkg_and_version = (
            (([pkg], python_version) for pkg in pkg_list))

        mock_config = mock.Mock()
        mock_config.PKG_LIST = pkg_list
        patch_config = mock.patch(
            'compatibility_lib.compatibility_checker.configs', mock_config)

        mock_concurrent = mock.Mock()
        mock_thread = mock.Mock()
        mock_concurrent.ThreadPoolExecutor.return_value = mock_thread
        mock_p = mock.Mock()
        mock_p.map.return_value = pkg_and_version
        mock_thread.__enter__ = mock.Mock(return_value=mock_p)
        mock_thread.__exit__ = mock.Mock(return_value=None)
        patch_concurrent = mock.patch(
            'compatibility_lib.compatibility_checker.concurrent.futures',
            mock_concurrent)

        res = []
        with patch_config, patch_concurrent:
            result = checker.get_self_compatibility(python_version)

            for item in result:
                res.append(item)

        self.assertTrue(mock_p.map.called)
        self.assertEqual(res, [((['pkg1'], 3),), ((['pkg2'], 3),)])

    def test_get_pairwise_compatibility(self):
        import itertools

        checker = compatibility_checker.CompatibilityChecker()

        pkg_list = ['pkg1', 'pkg2', 'pkg3']
        python_version = 3
        pkg_sets = itertools.combinations(pkg_list, 2)
        pkg_and_version = (
            (list(pkg_set), python_version) for pkg_set in pkg_sets)

        mock_config = mock.Mock()
        mock_config.PKG_LIST = pkg_list
        patch_config = mock.patch(
            'compatibility_lib.compatibility_checker.configs', mock_config)

        mock_concurrent = mock.Mock()
        mock_thread = mock.Mock()
        mock_concurrent.ThreadPoolExecutor.return_value = mock_thread
        mock_p = mock.Mock()
        mock_p.map.return_value = pkg_and_version
        mock_thread.__enter__ = mock.Mock(return_value=mock_p)
        mock_thread.__exit__ = mock.Mock(return_value=None)
        patch_concurrent = mock.patch(
            'compatibility_lib.compatibility_checker.concurrent.futures',
            mock_concurrent)

        res = []
        with patch_config, patch_concurrent:
            result = checker.get_pairwise_compatibility(python_version)

            for item in result:
                res.append(item)

        self.assertTrue(mock_p.map.called)
        self.assertEqual(res, [((['pkg1', 'pkg2'], 3),),
                               ((['pkg1', 'pkg3'], 3),),
                               ((['pkg2', 'pkg3'], 3),)])
