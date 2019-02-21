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
        checker = compatibility_checker.CompatibilityChecker()

        packages = ['opencensus']
        python_version = 3
        expected_server_url = 'http://104.197.8.72'

        data = {
            'python-version': python_version,
            'package': packages,
        }

        mock_requests = mock.Mock()
        mock_response = mock.Mock(content=b'{}')
        mock_requests.get.return_value = mock_response

        patch_request = mock.patch(
            'compatibility_lib.compatibility_checker.requests',
            mock_requests)

        with patch_request:
            checker.check(packages, python_version)

        mock_requests.get.assert_called_with(
            compatibility_checker.SERVER_URL, params=data, timeout=299)
        self.assertEqual(compatibility_checker.SERVER_URL,
                         expected_server_url)

    def _mock_retrying_check(self, *args):
        packages = args[0][0]
        python_version = args[0][1]
        return (packages, python_version, 'SUCCESS')

    def test_get_compatibility(self):
        checker = compatibility_checker.CompatibilityChecker()

        pkg_list = ['pkg1', 'pkg2', 'pkg3']
        pkg_py_version_not_supported = {
            2: ['tensorflow', ],
            3: ['apache-beam[gcp]', 'gsutil', ],
        }

        mock_config = mock.Mock()
        mock_config.PKG_LIST = pkg_list
        mock_config.PKG_PY_VERSION_NOT_SUPPORTED = pkg_py_version_not_supported
        patch_config = mock.patch(
            'compatibility_lib.compatibility_checker.configs', mock_config)

        patch_executor = mock.patch(
            'compatibility_lib.compatibility_checker.concurrent.futures.ThreadPoolExecutor',
            FakeExecutor)
        patch_retrying_check = mock.patch.object(
            compatibility_checker.CompatibilityChecker,
            'retrying_check',
            self._mock_retrying_check)

        res = []
        with patch_config, patch_executor, patch_retrying_check:
            result = checker.get_compatibility()

            for item in result:
                res.append(item)

        expected = sorted([
            ((['pkg1'], '2', 'SUCCESS'),),
            ((['pkg2'], '2', 'SUCCESS'),),
            ((['pkg3'], '2', 'SUCCESS'),),
            ((['pkg1'], '3', 'SUCCESS'),),
            ((['pkg2'], '3', 'SUCCESS'),),
            ((['pkg3'], '3', 'SUCCESS'),),
            ((['pkg1', 'pkg2'], '2', 'SUCCESS'),),
            ((['pkg1', 'pkg3'], '2', 'SUCCESS'),),
            ((['pkg2', 'pkg3'], '2', 'SUCCESS'),),
            ((['pkg1', 'pkg2'], '3', 'SUCCESS'),),
            ((['pkg1', 'pkg3'], '3', 'SUCCESS'),),
            ((['pkg2', 'pkg3'], '3', 'SUCCESS'),)])

        self.assertEqual(sorted(res), expected)


class FakeExecutor(object):
    def __init__(self, max_workers=10):
        self.max_workers = max_workers

    def map(self, check_func, pkgs):
        results = []

        for pkg in pkgs:
            results.append(check_func(pkg))

        return results

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return None
