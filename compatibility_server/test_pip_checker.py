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
import subprocess
import unittest

import pip_checker


class MockDockerClient(object):

    def __init__(self):
        self.containers = MockContainer()


class MockContainer(object):

    def __init__(self):
        self.is_running = False

    def create(self, image, command=None, **kwargs):
        return self

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def remove(self):
        pass

    def exec_run(self, cmd, stdout=True, stderr=True):
        _stdout = subprocess.PIPE if stdout else None
        _stderr = subprocess.PIPE if stderr else None
        result = subprocess.run(
            cmd, stderr=_stderr, stdout=_stdout)

        output = result.stdout if stdout else b''
        output += result.stderr if stderr else b''

        return result.returncode, output


class TestPipChecker(unittest.TestCase):

    def setUp(self):
        self._fake_pip_path = os.path.join(os.path.dirname(__file__),
                                           'fake_pip.py')

    @mock.patch.object(pip_checker._OneshotPipCheck, '_call_pypi_json_api')
    @mock.patch('pip_checker.docker.from_env')
    def test_success(self, mock_docker, mock__call_pypi_json_api):
        mock_docker.return_value=MockDockerClient()
        expected_list_output = [{
            'name': 'six',
            'version': '1.2.3',
            'latest_version': '1.2.4',
        }]
        expected_dependency_info = {
            'six': {
                'installed_version': '1.2.3',
                'installed_version_time': '2018-05-10T15:00:00',
                'latest_version': '1.2.4',
                'current_time': '2018-06-13T16:13:33.744591',
                'latest_version_time': '2018-06-13T18:29:51',
                'is_latest': False
            }
        }

        mock_datetime = mock.Mock()
        mock_now = mock.Mock()
        mock_now.isoformat.return_value = '2018-06-13T16:13:33.744591'
        mock_datetime.datetime.now.return_value = mock_now

        patch = mock.patch('pip_checker.datetime', mock_datetime)

        mock__call_pypi_json_api.return_value = {
            'releases': {
                '1.2.4': [
                    {
                        'upload_time': '2018-06-13T18:29:51',
                    },
                ],
                '1.2.3': [
                    {
                        'upload_time': '2018-05-10T15:00:00',
                    }
                ],
            },
        }

        expected_check_result = pip_checker.PipCheckResult(
            packages=['six'],
            result_type=pip_checker.PipCheckResultType.SUCCESS,
            result_text=None,
            dependency_info=expected_dependency_info)

        with patch:
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
    @mock.patch('pip_checker.docker.from_env')
    def test_success_with_clean(self, mock_docker, mock__call_pypi_json_api):
        mock_docker.return_value = MockDockerClient()
        expected_list_output = [{
            'name': 'six',
            'version': '1.2.3',
            'latest_version': '1.2.4',
        }]
        expected_dependency_info = {
            'six': {
                'installed_version': '1.2.3',
                'installed_version_time': '2018-05-10T15:00:00',
                'latest_version': '1.2.4',
                'current_time': '2018-06-13T16:13:33.744591',
                'latest_version_time': '2018-06-13T18:29:51',
                'is_latest': False
            }
        }

        mock_datetime = mock.Mock()
        mock_now = mock.Mock()
        mock_now.isoformat.return_value = '2018-06-13T16:13:33.744591'
        mock_datetime.datetime.now.return_value = mock_now

        patch = mock.patch('pip_checker.datetime', mock_datetime)

        mock__call_pypi_json_api.return_value = {
            'releases': {
                '1.2.4': [
                    {
                        'upload_time': '2018-06-13T18:29:51',
                    },
                ],
                '1.2.3': [
                    {
                        'upload_time': '2018-05-10T15:00:00',
                    }
                ],
            },
        }

        with patch:
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
            dependency_info=expected_dependency_info)

        self.assertEqual(
            check_result,
            expected_check_result)

    @mock.patch('pip_checker.docker.from_env')
    def test_install_failure(self, mock_docker):
        mock_docker.return_value = MockDockerClient()
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
                result_text=b'bad-install',
                dependency_info=None))

    @mock.patch.object(pip_checker._OneshotPipCheck, '_call_pypi_json_api')
    @mock.patch('pip_checker.docker.from_env')
    def test_check_warning(self, mock_docker, mock__call_pypi_json_api):
        mock_docker.return_value = MockDockerClient()
        expected_list_output = [{
            'name': 'six',
            'version': '1.2.3',
            'latest_version': '1.2.4',
        }]
        expected_dependency_info = {
            'six': {
                'installed_version': '1.2.3',
                'installed_version_time': '2018-05-10T15:00:00',
                'latest_version': '1.2.4',
                'current_time': '2018-06-13T16:13:33.744591',
                'latest_version_time': '2018-06-13T18:29:51',
                'is_latest': False
            }
        }

        mock_datetime = mock.Mock()
        mock_now = mock.Mock()
        mock_now.isoformat.return_value = '2018-06-13T16:13:33.744591'
        mock_datetime.datetime.now.return_value = mock_now

        patch = mock.patch('pip_checker.datetime', mock_datetime)

        mock__call_pypi_json_api.return_value = {
            'releases': {
                '1.2.4': [
                    {
                        'upload_time': '2018-06-13T18:29:51',
                    },
                ],
                '1.2.3': [
                    {
                        'upload_time': '2018-05-10T15:00:00',
                    }
                ],
            },
        }

        with patch:
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
                result_text=b'',
                dependency_info=expected_dependency_info)

        self.assertEqual(
            check_result,
            expected_check_result)

    @mock.patch('pip_checker.docker.from_env')
    def test_freeze_error(self, mock_docker):
        mock_docker.return_value = MockDockerClient()
        with self.assertRaises(pip_checker.PipError) as e:
            pip_checker.check(
                pip_command=[self._fake_pip_path, '--freeze-returncode=1'],
                packages=['six'], clean=True)
        self.assertIn('freeze', e.exception.command)

    @mock.patch('pip_checker.docker.from_env')
    def test_uninstall_error(self, mock_docker):
        mock_docker.return_value = MockDockerClient()
        with self.assertRaises(pip_checker.PipError) as e:
            pip_checker.check(
                pip_command=[
                    self._fake_pip_path, '--expected-install-args=-U,six',
                    '--uninstall-returncode=1', '--freeze-output=six==1.2.3\n'
                ],
                packages=['six'],
                clean=True)
        self.assertIn('uninstall', e.exception.command)
