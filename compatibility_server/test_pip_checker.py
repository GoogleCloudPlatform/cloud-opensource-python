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

import calendar
import datetime
import json
import mock
import os.path
import subprocess
import unittest

import pip_checker


def timestamp_to_seconds(timestamp: str) -> int:
    """Convert a timestamp string into a seconds value
    
    Args:
        timestamp: An ISO 8601 format string returned by calling isoformat()
            on a `datetime.datetime` type timestamp.

    Returns:
        Timestamp in seconds.
    """
    ISO_DATETIME_REGEX = '%Y-%m-%dT%H:%M:%S.%fZ'
    timestamp_str = datetime.datetime.strptime(timestamp, ISO_DATETIME_REGEX)
    epoch_time_secs = calendar.timegm(timestamp_str.timetuple())
    return epoch_time_secs


class MockDockerClient(object):

    def __init__(self):
        self.containers = MockContainer()


class MockContainer(object):

    def __init__(self):
        self.is_running = False
        self.start_time = None

    def create(self, image, command=None, **kwargs):
        return self

    def start(self):
        self.is_running = True

    def stop(self, timeout=10):
        self.is_running = False

    def run(self,
            base_image,
            command,
            detach=True,
            remove=False,
            auto_remove=False):
        from datetime import datetime

        self.start_time = timestamp_to_seconds(
            datetime.utcnow().isoformat() + 'Z')
        return self

    def exec_run(self, cmd, stdout=True, stderr=True):
        from datetime import datetime

        _stdout = subprocess.PIPE if stdout else None
        _stderr = subprocess.PIPE if stderr else None
        result = subprocess.run(
            cmd, stderr=_stderr, stdout=_stdout)

        output = result.stdout if stdout else b''
        output += result.stderr if stderr else b''

        current_time = timestamp_to_seconds(
            datetime.utcnow().isoformat() + 'Z')
        duration = current_time - self.start_time

        if duration > pip_checker.TIME_OUT:
            result.returncode = 137
            output = b''

        return result.returncode, output


class TestPipChecker(unittest.TestCase):

    def setUp(self):
        self._fake_pip_path = os.path.join(os.path.dirname(__file__),
                                           'fake_pip.py')

    def test__run_command_success(self):
        checker = pip_checker._OneshotPipCheck(
            ['python3', '-m', 'pip'], packages=['six'])
        container = checker._run_container(MockDockerClient())

        returncode, output = checker._run_command(
            container,
            ["echo", "testing"],
            stdout=True,
            stderr=True,
            raise_on_failure=False)

        self.assertEqual(output, 'testing\n')

    def test__run_command_timeout(self):
        checker = pip_checker._OneshotPipCheck(
            ['python3', '-m', 'pip'], packages=['six'])

        TIME_OUT = 0.1
        patch_timeout = mock.patch('pip_checker.TIME_OUT', TIME_OUT)

        with patch_timeout, self.assertRaises(pip_checker.PipCheckerError):
            container = checker._run_container(MockDockerClient())
            checker._run_command(
                container,
                ["sleep", "1"],
                stdout=True,
                stderr=True,
                raise_on_failure=False)

    @mock.patch.object(pip_checker._OneshotPipCheck, '_call_pypi_json_api')
    @mock.patch('pip_checker.docker.from_env')
    def test_success(self, mock_docker, mock__call_pypi_json_api):
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
                result_text='bad-install',
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
                    '--check-output=package has requirement A, but you have B',
                    '--freeze-output=six==1.2.3\n',
                    '--list-output={}'.format(
                        json.dumps(expected_list_output))
                ],
                packages=['six'])
        expected_check_result = pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.CHECK_WARNING,
                result_text='package has requirement A, but you have B',
                dependency_info=expected_dependency_info)

        self.assertEqual(
            check_result,
            expected_check_result)
