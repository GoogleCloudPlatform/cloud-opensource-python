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

"""Tests for pip_checker.

Uses a script "fake_pip.py" to simulate the behavior of the pip
(https://pypi.org/project/pip/) installation tool.
"""

import json
import mock
import os.path
import unittest

import pip_checker


class TestPipChecker(unittest.TestCase):

    def setUp(self):
        self._fake_pip_path = os.path.join(os.path.dirname(__file__),
                                           'fake_pip.py')

    @mock.patch.object(pip_checker._OneshotPipCheck, '_call_pypi_json_api')
    def test_success(self, mock__call_pypi_json_api):
        expected_list_output = [{
            'name': 'six',
            'version': '1.2.3',
            'latest_version': '1.2.4',
        }]
        expected_version_and_date = {
            'six': {
                'version': '1.2.3',
                'latest_version': '1.2.4',
                'release_date': '2018-06-13',
            }
        }

        mock__call_pypi_json_api.return_value = {
            'releases': {
                '1.2.4': [
                    {
                        'upload_time': '2018-06-13',
                    },
                ],
            },
        }

        expected_check_result = pip_checker.PipCheckResult(
            packages=['six'],
            result_type=pip_checker.PipCheckResultType.SUCCESS,
            result_text=None,
            requirements='six==1.2.3\n',
            version_and_date=expected_version_and_date)
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--expected-install-args=-U,six',
                '--freeze-output=six==1.2.3\n',
                '--list-output={}'.format(
                    json.dumps(expected_list_output))
            ],
            packages=['six'])
        self.assertEqual(
            check_result,
            expected_check_result)

    @mock.patch.object(pip_checker._OneshotPipCheck, '_call_pypi_json_api')
    def test_success_with_clean(self, mock__call_pypi_json_api):
        expected_list_output = [{
            'name': 'six',
            'version': '1.2.3',
            'latest_version': '1.2.4',
        }]
        expected_version_and_date = {
            'six': {
                'version': '1.2.3',
                'latest_version': '1.2.4',
                'release_date': '2018-06-13',
            }
        }

        mock__call_pypi_json_api.return_value = {
            'releases': {
                '1.2.4': [
                    {
                        'upload_time': '2018-06-13',
                    },
                ],
            },
        }
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--expected-install-args=-U,six',
                '--uninstall-returncode=0', '--freeze-output=six==1.2.3\n',
                '--list-output={}'.format(
                    json.dumps(expected_list_output))
            ],
            packages=['six'],
            clean=True)
        expected_check_result = pip_checker.PipCheckResult(
            packages=['six'],
            result_type=pip_checker.PipCheckResultType.SUCCESS,
            result_text=None,
            requirements='six==1.2.3\n',
            version_and_date=expected_version_and_date)

        self.assertEqual(
            check_result,
            expected_check_result)

    def test_install_failure(self):
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--expected-install-args=-U,six',
                '--install-returncode=1', '--install-output=bad-install'
            ],
            packages=['six'])
        self.assertEqual(
            check_result,
            pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.INSTALL_ERROR,
                result_text='bad-install',
                requirements=None,
                version_and_date=None))

    @mock.patch.object(pip_checker._OneshotPipCheck, '_call_pypi_json_api')
    def test_check_warning(self, mock__call_pypi_json_api):
        expected_list_output = [{
            'name': 'six',
            'version': '1.2.3',
            'latest_version': '1.2.4',
        }]
        expected_version_and_date = {
            'six': {
                'version': '1.2.3',
                'latest_version': '1.2.4',
                'release_date': '2018-06-13',
            }
        }

        mock__call_pypi_json_api.return_value = {
            'releases': {
                '1.2.4': [
                    {
                        'upload_time': '2018-06-13',
                    },
                ],
            },
        }

        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path,
                '--check-returncode=1',
                '--check-output=bad-check',
                '--freeze-output=six==1.2.3\n',
                '--list-output={}'.format(
                    json.dumps(expected_list_output))
            ],
            packages=['six'])
        expected_check_result = pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.CHECK_WARNING,
                result_text='bad-check',
                requirements='six==1.2.3\n',
                version_and_date=expected_version_and_date)

        self.assertEqual(
            check_result,
            expected_check_result)

    def test_freeze_error(self):
        with self.assertRaises(pip_checker.PipError) as e:
            pip_checker.check(
                pip_command=[self._fake_pip_path, '--freeze-returncode=1'],
                packages=['six'])
        self.assertIn('freeze', e.exception.command)

    def test_uninstall_error(self):
        with self.assertRaises(pip_checker.PipError) as e:
            pip_checker.check(
                pip_command=[
                    self._fake_pip_path, '--expected-install-args=-U,six',
                    '--uninstall-returncode=1', '--freeze-output=six==1.2.3\n'
                ],
                packages=['six'],
                clean=True)
        self.assertIn('uninstall', e.exception.command)
