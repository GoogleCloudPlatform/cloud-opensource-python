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

"""Installs packages using pip and tests them for version compatibility.

Conceptually, it runs:
  $ pip install <packages> 2>out.txt && \\
    (pip check >out.txt; \\
     pip freeze >requirements.txt)
and returns the contents of "out.txt" and "requirements.txt".

See https://pip.pypa.io/en/stable/user_guide/.
"""

import datetime
import enum
import json
import logging
import os.path
import shlex
import tempfile
import urllib.request

from typing import Any, List, Mapping, Optional

import docker

PYPI_URL = 'https://pypi.org/pypi/'
CONTAINER_WITH_PKG = "checker"


class PipCheckerError(Exception):
    """A pip or docker command failed in an unexpected way."""

    def __init__(self, error_msg, command='', returncode=None):
        super(PipCheckerError, self).__init__(
            'Command ({command}) failed with error [{returncode}], '
            'logs are: {error_msg}'.format(
                command=command, returncode=returncode,
                error_msg=error_msg))

        # Convert error_msg to bytes as this needed to be returned in the
        # response which should be bytes. And the message returned from docker
        # is already bytes so that won't need the conversion.
        if isinstance(error_msg, str):
            self.error_msg = error_msg.encode('utf-8')
        else:
            self.error_msg = error_msg

        self.command = command
        self.returncode = returncode

    @property
    def command_string(self) -> str:
        return ' '.join(shlex.quote(c) for c in self.command)


@enum.unique
class PipCheckResultType(enum.Enum):
    """The combined results of "pip install" and "pip check".

    SUCCESS: Indicates that "pip install <packages> && pip check" completed
        successfully.
    INSTALL_ERROR: Indicates that "pip install <packages>" failed.
    CHECK_WARNING: Indicates that "pip check" completed with a non-zero exit
        code.
    """
    SUCCESS = 'success'
    INSTALL_ERROR = 'install_error'
    CHECK_WARNING = 'check_warning'


class PipCheckResult:
    """The results of "pip install <packages> && pip check".

    Attributes:
        packages: The list of packages that were installed
            e.g. ['tensorflow', 'numpy'].
        result_type: The result of "pip install <packages> && pip check".
        result_text: The text output of "pip install && pip check". For
            example: "Could not find a version that satisfies the requirement
            tensorflow." or "numpy has requirement six<3, but you have six
            4.0.1."
            Will be None if "pip install <packages> && pip check" completed
            without error.
        dependency_info: The text output of "pip list" i.e. the packages that
            were installed as a product of the "pip install <packages>"
            command. Dict which stores the dependency versions and latest
            release time, together with the timestamp that run this check.

            e.g. "dependency_info": {
                    "astroid": {
                        "installed_version": "1.6.5",
                        "latest_version": "1.6.5",
                        "current_time": "2018-06-14T13:46:04.180159",
                        "latest_version_time": "2018-06-06T15:08:26",
                        "is_latest": true
                    },
                    ...
                }
    """

    def __init__(self,
                 packages: List[str],
                 result_type: PipCheckResultType,
                 result_text: Optional[str] = None,
                 dependency_info: Optional[Mapping[str, Any]] = None):
        """Initializer for PipCheckResult/

        Args:
            packages: The list of packages that were installed
                e.g. ['tensorflow', 'numpy'].
            result_type: The result of "pip install <packages> && pip check".
            result_text: The text output of "pip install && pip check".
            dependency_info: The text output of "pip list" i.e. the packages
                that were installed as a product of the "pip install <packages"
                command. And also the latest release date get by querying
                Pypi json API and the timestamp when running this check.
        """

        self._packages = packages
        self._result_type = result_type
        self._result_text = result_text
        self._dependency_info = dependency_info

    def __eq__(self, other):
        return (isinstance(other, PipCheckResult) and
                self.packages == other.packages and
                self.result_type == other.result_type and
                self.result_text == other.result_text and
                self.dependency_info == other.dependency_info)

    def __repr__(self):
        return ('PipCheckResult(packages={!r}, result_type={!r}, ' +
                'result_text={!r}, dependency_info={!r})').format(
            self.packages,
            self.result_type,
            self.result_text,
            self.dependency_info)

    def with_extra_attrs(self, dependency_info: Optional[str] = None):
        """Return a new PipCheckResult with extra attributes."""
        return PipCheckResult(self.packages,
                              self.result_type,
                              self.result_text,
                              dependency_info=dependency_info)

    @property
    def packages(self) -> List[str]:
        return self._packages

    @property
    def result_type(self) -> PipCheckResultType:
        return self._result_type

    @property
    def result_text(self) -> Optional[str]:
        return self._result_text

    @property
    def dependency_info(self) -> Optional[Mapping[str, Any]]:
        return self._dependency_info


class _OneshotPipCheck():
    """Execute a single pip version compatibility check.

    Conceptually, it runs:
      $ pip install <packages> 2>out.txt && \\
        (pip check >out.txt; \\
         pip freeze >requirements.txt)
    and returns the contents of "out.txt" and "requirements.txt".

    See https://pip.pypa.io/en/stable/user_guide/.
    """

    def __init__(self,
                 pip_command: List[str],
                 packages: List[str]):
        """Initializes _OneshotPipCheck with the arguments needed to run pip.

        Args:
            pip_command: The arguments to use when invoking pip e.g.
                ['python3', '-m', 'pip'].
            packages: The packages to check for compatibility e.g.
                ['numpy', 'tensorflow'].
        """
        self._pip_command = pip_command
        self._packages = packages
        self._docker_client = docker.from_env()
        self._container = self._build_container

    def _get_base_image(self):
        """Get the base image name based on Python version."""
        python_version = self._pip_command[0]

        if python_version == 'python2':
            base_image = "python:2.7"
        else:
            base_image = "python:3.6"

        return base_image

    @property
    def _build_container(self):
        """Build the container which contains a Python interpreter."""
        base_image = self._get_base_image()

        try:
            container = self._docker_client.containers.create(
                base_image,
                command="/bin/bash",
                tty=True,
                stdin_open=True)
            container.start()
        except docker.errors.APIError:
            raise PipCheckerError(
                error_msg="Error occurs when creating docker container.")

        return container

    def _cleanup_container(self):
        """Stop and remove the container."""
        try:
            self._container.stop()
            self._container.remove()
        except docker.errors.APIError:
            raise PipCheckerError(
                error_msg="Error occurs when cleaning up docker container.")

    def _run_command(self, command, stdout, stderr, raise_on_failure=True):
        """Run docker commands using docker python sdk.

        Args:
            command (str): The command to run in docker container.
            stdout (boolean): Whether to include stdout in output.
            stderr (boolean): Whether to include stderr in output.
            raise_on_failure (boolean): Whether to raise on failure.

        Returns:
            A tuple containing returncode and output.
        """
        returncode, output = self._container.exec_run(
            command, stdout=stdout, stderr=stderr)

        if returncode and raise_on_failure:
            raise PipCheckerError(error_msg=output,
                                  command=command,
                                  returncode=returncode)

        return returncode, output

    @staticmethod
    def _call_pypi_json_api(pkg_name, pkg_version):
        """Call PyPI json api to get the dependency info."""
        pypi_pkg_url = PYPI_URL + '{}/{}/json'.format(pkg_name, pkg_version)

        try:
            r = urllib.request.Request(pypi_pkg_url)

            with urllib.request.urlopen(r) as f:
                result = json.loads(f.read().decode('utf-8'))
        except urllib.error.HTTPError:
            logging.error('Package {} with version {} not found in Pypi'.
                          format(pkg_name, pkg_version))
            return None
        return result

    def _build_command(self, subcommands):
        """Build pip commands."""
        return self._pip_command + subcommands

    def _install(self):
        """Run pip install in the container."""
        command = self._build_command(['install', '-U'] + self._packages)
        returncode, output = self._run_command(
            command, stdout=False, stderr=True, raise_on_failure=False)
        if returncode:
            return PipCheckResult(self._packages,
                                  PipCheckResultType.INSTALL_ERROR,
                                  output)
        return PipCheckResult(self._packages, PipCheckResultType.SUCCESS)

    def _check(self):
        """Run pip check to detect if there are any version conflicts."""
        command = self._build_command(['check'])

        # The returncode is non-zero if there are conflicts,
        # shouldn't raise on this.
        returncode, output = self._run_command(
            command, stdout=False, stderr=True, raise_on_failure=False)
        if returncode:
            return PipCheckResult(self._packages,
                                  PipCheckResultType.CHECK_WARNING,
                                  output)
        return PipCheckResult(self._packages, PipCheckResultType.SUCCESS)

    def _list(self):
        """Run pip list to get the outdated packages and dependency info."""
        """Use pypi json api to get the release date of the latest version."""
        pkg_version_date = {}

        # Get the package installed version and latest version
        command = self._build_command(['list', '--format=json'])
        _, list_all = self._run_command(
            command, stdout=True, stderr=False, raise_on_failure=False)

        pip_list_result = json.loads(list_all.decode('utf-8'))

        command = self._build_command(['list', '-o', '--format=json'])
        _, list_outdated = self._run_command(
            command, stdout=True, stderr=False, raise_on_failure=False)

        pip_list_latest_result = json.loads(list_outdated.decode('utf-8'))

        # Get the outdated packages and latest versions
        outdated_pkgs = {}

        for pkg in pip_list_latest_result:
            pkg_name = pkg.get('name')
            latest_version = pkg.get('latest_version')
            outdated_pkgs[pkg_name] = latest_version

        for pkg in pip_list_result:
            pkg_name = pkg.get('name')
            installed_version = pkg.get('version')
            latest_version = installed_version

            is_latest = True
            if pkg_name in outdated_pkgs:
                latest_version = outdated_pkgs.get(pkg_name)
                # For py2, pip list -o returns all the packages but not just
                # the outdated pkgs.
                if latest_version != installed_version:
                    is_latest = False

            # Get the package latest version release date
            result = self._call_pypi_json_api(pkg_name, latest_version)

            # For each release versions, first item is wheel file,
            # second is tar.gz file, we use the time of the wheel file.
            installed_version_time = None
            latest_version_time = None
            if result is not None:
                if 'releases' in result:
                    latest_release = result.get('releases').get(
                        latest_version)
                    installed_release = result.get('releases').get(
                        installed_version)
                    if latest_release:
                        latest_version_time = latest_release[0].get(
                            'upload_time')
                    if installed_release:
                        installed_version_time = installed_release[0].get(
                            'upload_time')

            pkg_info = {
                'installed_version': installed_version,
                'installed_version_time': installed_version_time,
                'latest_version': latest_version,
                'current_time': datetime.datetime.now().isoformat(),
                'latest_version_time': latest_version_time,
                'is_latest': is_latest,
            }

            pkg_version_date[pkg_name] = pkg_info

        return pkg_version_date

    def run(self):
        """Run the version compatibility check."""
        install_result = self._install()

        dependency_info = None
        if install_result.result_type != PipCheckResultType.INSTALL_ERROR:
            dependency_info = self._list()

        if install_result.result_type == PipCheckResultType.SUCCESS:
            install_result = self._check()

        self._cleanup_container()

        return install_result.with_extra_attrs(
            dependency_info=dependency_info)


def check(pip_command: List[str],
          packages: List[str]) -> PipCheckResultType:
    """Runs a version compatibility check using the given packages.

    Conceptually, it runs:
      $ pip install <packages> 2>out.txt && \\
        (pip check >out.txt; \\
         pip freeze >requirements.txt)
    and returns the contents of "out.txt" and "requirements.txt".

    See https://pip.pypa.io/en/stable/user_guide/.

    Args:
        pip_command: The arguments to use when invoking pip e.g.
            ['python3', '-m', 'pip'].
        packages: The packages to check for compatibility e.g.
            ['numpy', 'tensorflow'].
    """
    return _OneshotPipCheck(pip_command, packages).run()
