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
import re
import shlex
import urllib.request

from typing import Any, List, Mapping, Optional, Tuple

import docker

PYPI_URL = 'https://pypi.org/pypi/'
CONTAINER_WITH_PKG = "checker"
TIME_OUT = 300  # seconds

# Pattern for pip installation errors not related to the package being
# installed. See:
# https://github.com/pypa/pip/blob/3a77bd667cc68935040563e1351604c461ce5333/src/pip/_internal/commands/install.py#L533
PIP_ENVIRONMENT_ERROR_PATTERN = re.compile(
    r'not install packages due to an EnvironmentError: (?P<error>.*)')

# Pattern for pip check results of version conflicts
PIP_CHECK_CONFLICTS_PATTERN = re.compile(
    r'(.*)has requirement(.*)but you have(.*)')


class PipCheckerError(Exception):
    """Pip checker failed in an unexpected way."""

    def __init__(self, error_msg: str):
        super(PipCheckerError, self).__init__(
            'Pip Checker failed: {error_msg}'.format(error_msg=error_msg))

        self.error_msg = error_msg


class PipError(PipCheckerError):
    """A pip command failed in an unexpected way."""

    def __init__(self,
                 error_msg: str,
                 command: List[str],
                 returncode: int):
        command_string = ' '.join(shlex.quote(c) for c in command)
        super(PipError, self).__init__(
            'Pip command ({command_string}) failed with error [{returncode}]: '
            '{error_msg}'.format(
                command_string=command_string, returncode=returncode,
                error_msg=error_msg))

        self.command = command
        self.returncode = returncode
        self.command_string = command_string


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

    def _get_base_image(self):
        """Get the base image name based on Python version."""
        python_version = self._pip_command[0]

        if python_version == 'python2':
            base_image = "python:2.7"
        else:
            base_image = "python:3.6"

        return base_image

    def _run_container(self,
                       docker_client) -> docker.models.containers.Container:
        """Build the container which contains a Python interpreter."""
        base_image = self._get_base_image()

        try:
            # The timeout for running the commands is 300 seconds.
            # Container will stop running after the timeout.
            container = docker_client.containers.run(
                base_image,
                command="sleep {}".format(TIME_OUT),
                # Remove the container when this process stops or the container
                # stops running. Needed to prevent unbounded growth in storage
                # used for virtual file systems (because each check creates a
                # new container). Run `docker system prune -a -f` to manually
                # remove old containers.
                auto_remove=True,  # Remove the container if this process ends.
                remove=True,  # Remove the container when it finishes.
                detach=True)
        except docker.errors.APIError as e:
            raise PipCheckerError(
                error_msg="An error occurred while starting a docker "
                          "container. Error message: {}".format(e.explanation))
        except IOError as e:
            # TODO: Log the exception and monitor it after trying to decode
            # this into a requests.exception.* e.g. ReadTimeout. See:
            # http://docs.python-requests.org/en/master/_modules/requests/exceptions/
            raise PipCheckerError(
                error_msg="An error occurred while starting a docker "
                          "container. Error message: {}".format(e))

        return container

    def _cleanup_container(self,
                           container: docker.models.containers.Container):
        """Stop the container and remove it's associated storage."""
        try:
            container.stop(timeout=0)
        except (docker.errors.APIError, docker.errors.NotFound):
            raise PipCheckerError(
                error_msg="Error occurs when cleaning up docker container."
                          "Container does not exist.")
        except IOError as e:
            # TODO: Log the exception and monitor it after trying to decode
            # this into a requests.exception.* e.g. ReadTimeout. See:
            # http://docs.python-requests.org/en/master/_modules/requests/exceptions/
            raise PipCheckerError(
                error_msg="An error occurred while stopping a docker"
                          "container. Error message: {}".format(e))

    def _run_command(
            self,
            container: docker.models.containers.Container,
            command: List[str],
            stdout: bool,
            stderr: bool,
            raise_on_failure: Optional[bool] = True) -> Tuple[int, str]:
        """Run docker commands using docker python sdk.

        Args:
            container: The docker container that runs this command.
            command: The command to run in docker container.
            stdout: Whether to include stdout in output.
            stderr: Whether to include stderr in output.
            raise_on_failure: Whether to raise on failure.

        Returns:
            A tuple containing the return code of the given command and the
            output of that command.
        """
        try:
            returncode, output = container.exec_run(
                command, stdout=stdout, stderr=stderr)

            output = output.decode('utf-8')
        except docker.errors.APIError as e:
            # Clean up the container if command fails
            self._cleanup_container(container)
            raise PipCheckerError(error_msg="Error occurs when executing "
                                            "commands in container."
                                            "Error message: "
                                            "{}".format(e.explanation))
        except IOError as e:
            # TODO: Log the exception and monitor it after trying to decode
            # this into a requests.exception.* e.g. ReadTimeout. See:
            # http://docs.python-requests.org/en/master/_modules/requests/exceptions/
            raise PipCheckerError(
                error_msg="An error occurred while running the command {} in"
                          "container. Error message: {}".format(command, e))

        if returncode and raise_on_failure:
            raise PipError(error_msg=output,
                           command=command,
                           returncode=returncode)

        return returncode, output

    @staticmethod
    def _call_pypi_json_api(pkg_name: str, pkg_version: str):
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

    def _build_command(self, subcommands: List[str]):
        """Build pip commands."""
        return self._pip_command + subcommands

    def _install(self, container: docker.models.containers.Container):
        """Run pip install in the container."""
        command = self._build_command(['install', '-U'] + self._packages)
        returncode, output = self._run_command(
            container,
            command,
            stdout=False,
            stderr=True,
            raise_on_failure=False)
        if returncode:
            environment_error = PIP_ENVIRONMENT_ERROR_PATTERN.search(output)
            if environment_error:
                raise PipError(error_msg=environment_error.group('error'),
                               command=command,
                               returncode=returncode)

            return PipCheckResult(self._packages,
                                  PipCheckResultType.INSTALL_ERROR,
                                  output)
        return PipCheckResult(self._packages, PipCheckResultType.SUCCESS)

    def _check(self, container: docker.models.containers.Container):
        """Run pip check to detect if there are any version conflicts."""
        command = self._build_command(['check'])

        # The returncode is non-zero if there are conflicts,
        # shouldn't raise on this.
        returncode, output = self._run_command(
            container,
            command,
            stdout=True,
            stderr=True,
            raise_on_failure=False)

        has_version_conflicts = PIP_CHECK_CONFLICTS_PATTERN.search(output)
        if returncode and has_version_conflicts:
            return PipCheckResult(self._packages,
                                  PipCheckResultType.CHECK_WARNING,
                                  output)
        return PipCheckResult(self._packages, PipCheckResultType.SUCCESS)

    def _list(self, container: docker.models.containers.Container):
        """Return dependency information.

        Args:
            container: The docker container to run the check in.

        Returns:
            A mapping between packages names, returned by `pip list`, to
            information about that package. The package information is
            represented by a dictionary with the following format:

            {
                "installed_version": The installed version of the package
                    e.g. "1.2.3".
                "installed_version_time": The release date of the package that
                    is installed as a ISO 8601 string
                    e.g. "2018-12-11T19:51:02".
                "latest_version": The latest version of the package
                    e.g. "2.1.1".
                "latest_version_time": The release time of the latest version
                    of the package as an ISO 8601 string
                    e.g. "2018-12-11T19:51:02".
                "current_time": The current time as a ISO 8601 strings
                    e.g. "2018-12-11T19:51:02".
                "is_latest": A boolean indicating whether the installed package
                    version is the latest version.
            }

            For example:
            {
                "setuptools": {
                    "installed_version": "40.6.3",
                    "installed_version_time": "2018-12-11T19:51:02",
                    "latest_version": "40.6.3",
                    "current_time": "2019-01-18T21:09:15.187775",
                    "latest_version_time": "2018-12-11T19:51:02",
                    "is_latest": True
                },
                "wheel": {
                    "installed_version": "0.32.3",
                    "installed_version_time": "2018-11-19T00:25:58",
                    "latest_version": "0.32.3",
                    "current_time": "2019-01-18T21:09:15.170863",
                    "latest_version_time": "2018-11-19T00:25:58",
                    "is_latest": True
                }
            }
        """

        """Use pypi json api to get the release date of the latest version."""
        pkg_version_date = {}

        # Get the package installed version and latest version
        command = self._build_command(['list', '--format=json'])
        _, list_all = self._run_command(
            container,
            command,
            stdout=True,
            stderr=False,
            raise_on_failure=True)

        pip_list_result = json.loads(list_all)

        command = self._build_command(['list', '-o', '--format=json'])
        _, list_outdated = self._run_command(
            container,
            command,
            stdout=True,
            stderr=False,
            raise_on_failure=True)

        pip_list_latest_result = json.loads(list_outdated)

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

    def run(self) -> PipCheckResult:
        """Run the version compatibility check."""

        # Create docker client and start running the container
        docker_client = docker.from_env()
        container = self._run_container(docker_client)

        try:
            install_result = self._install(container)

            dependency_info = None
            if install_result.result_type != PipCheckResultType.INSTALL_ERROR:
                dependency_info = self._list(container)

            if install_result.result_type == PipCheckResultType.SUCCESS:
                install_result = self._check(container)

            return install_result.with_extra_attrs(
                dependency_info=dependency_info)
        finally:
            self._cleanup_container(container)


def check(pip_command: List[str],
          packages: List[str]) -> PipCheckResult:
    """Runs a version compatibility check using the given packages.

    Conceptually, it runs:
    $ pip install <packages> 2>out.txt
    $ pip list --format=json >deps.txt
    $ pip check >out.txt

    See https://pip.pypa.io/en/stable/user_guide/.

    Args:
        pip_command: The arguments to use when invoking pip e.g.
            ['python3', '-m', 'pip'].
        packages: The packages to check for compatibility e.g.
            ['numpy', 'tensorflow'].

    Returns:
        A PipCheckResult representing the result of the compatibility check.
    """
    return _OneshotPipCheck(pip_command, packages).run()
