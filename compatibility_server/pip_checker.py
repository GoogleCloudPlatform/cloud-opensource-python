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

import enum
import logging
import os.path
import shlex
import subprocess
import tempfile

from typing import List, Optional


class PipError(Exception):
    """A pip command failed in an unexpected way."""

    def __init__(self, command: List[str], returncode: int, stderr_path: str):
        super(PipError, self).__init__(
            'pip command ({command}) failed with error [{returncode}], '
            'logs at: {stderr_path}'.format(
                command=command, returncode=returncode,
                stderr_path=stderr_path))
        self.command = command
        self.returncode = returncode
        self.stderr_path = stderr_path

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
        requirements: The text output of "pip freeze" i.e. the packages that
            were installed as a product of the "pip install <packages" command.
            The output can be parsed with pkg_resources.parse_requirements().
            For example: "numpy==1.23\nsix==3.4.5". Will be None if a previous
            step failed e.g. "pip install <packages>".
    """

    def __init__(self,
                 packages: List[str],
                 result_type: PipCheckResultType,
                 result_text: Optional[str] = None,
                 requirements: Optional[str] = None):
        """Initializer for PipCheckResult/

        Args:
            packages: The list of packages that were installed
                e.g. ['tensorflow', 'numpy'].
            result_type: The result of "pip install <packages> && pip check".
            result_text: The text output of "pip install && pip check".
            requirements: The text output of "pip freeze" i.e. the packages
                that were installed as a product of the "pip install <packages"
                command.
        """

        self._packages = packages
        self._result_type = result_type
        self._result_text = result_text
        self._requirements = requirements

    def __eq__(self, other):
        return (isinstance(other, PipCheckResult) and
                self.packages == other.packages and
                self.result_type == other.result_type and
                self.result_text == other.result_text and
                self.requirements == other.requirements)

    def __repr__(self):
        return ('PipCheckResult(packages={!r}, result_type={!r}, ' +
                'result_text={!r}, requirements={!r})').format(
            self.packages, self.result_type, self.result_text,
            self.requirements)

    def with_requirements(self, requirements: str):
        """Return a new PipCheckResult with a new "requirements" attribute."""
        return PipCheckResult(self.packages,
                              self.result_type,
                              self.result_text,
                              requirements)

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
    def requirements(self) -> Optional[str]:
        return self._requirements


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
                 packages: List[str],
                 tmp_path: str,
                 clean: bool):
        """Initializes _OneshotPipCheck with the arguments needed to run pip.

        Args:
            pip_command: The arguments to use when invoking pip e.g.
                ['python3', '-m', 'pip'].
            packages: The packages to check for compatibility e.g.
                ['numpy', 'tensorflow'].
            tmp_path: The file system path to use for temporary files
                e.g."/tmp".
            clean: If True then all previously installed packages will be
                uninstalled before installing "packages".
        """
        self._pip_command = pip_command
        self._packages = packages
        self._tmp_path = tmp_path
        self._output_directory = None
        self._clean = clean

    @staticmethod
    def _run_command(command, stdout_path, stderr_path, raise_on_failure=True):
        with open(stdout_path, 'w') as stdout_file, open(stderr_path,
                                                         'w') as stderr_file:
            completed_command = subprocess.run(
                command, stdout=stdout_file, stderr=stderr_file)

        logging.debug('Running %s [returncode=%s]', command,
                      completed_command.returncode)
        if completed_command.returncode and raise_on_failure:
            raise PipError(command, completed_command.returncode, stderr_path)

        return completed_command.returncode

    def _build_command(self, subcommands):
        return self._pip_command + subcommands

    def _freeze(self, requirements_file_path):
        command = self._build_command(['freeze'])
        std_err_path = os.path.join(self._output_directory, 'freeze-error.txt')
        self._run_command(command, requirements_file_path, std_err_path)

    def _uninstall(self, requirements_file_path):
        std_out_path = os.path.join(self._output_directory,
                                    'uninstall-out.txt')
        std_err_path = os.path.join(self._output_directory,
                                    'uninstall-error.txt')
        command = self._build_command(
            ['uninstall', '--yes', '-r', requirements_file_path])
        self._run_command(command, std_out_path, std_err_path)

    def _read(self, path):
        with open(path) as f:
            return f.read()

    def _install(self):
        std_out_path = os.path.join(self._output_directory,
                                    'install-out.txt')
        std_err_path = os.path.join(self._output_directory,
                                    'install-error.txt')
        command = self._build_command(['install', '-U'] + self._packages)
        returncode = self._run_command(
            command, std_out_path, std_err_path, raise_on_failure=False)
        if returncode:
            return PipCheckResult(self._packages,
                                  PipCheckResultType.INSTALL_ERROR,
                                  self._read(std_err_path))
        return PipCheckResult(self._packages, PipCheckResultType.SUCCESS)

    def _check(self):
        std_out_path = os.path.join(self._output_directory, 'check-out.txt')
        std_err_path = os.path.join(self._output_directory, 'check-error.txt')
        command = self._build_command(['check'])
        returncode = self._run_command(
            command, std_out_path, std_err_path, raise_on_failure=False)
        if returncode:
            return PipCheckResult(self._packages,
                                  PipCheckResultType.CHECK_WARNING,
                                  self._read(std_out_path))
        return PipCheckResult(self._packages, PipCheckResultType.SUCCESS)

    def run(self):
        """Run the version compatibility check."""
        self._output_directory = tempfile.mkdtemp(dir=self._tmp_path)
        if self._clean:
            requirements_old_file_path = os.path.join(self._output_directory,
                                                      'requirements-old.txt')
            self._freeze(requirements_old_file_path)
            if os.path.getsize(requirements_old_file_path) > 0:
                self._uninstall(requirements_old_file_path)
        install_result = self._install()

        requirements = None
        if install_result.result_type != PipCheckResultType.INSTALL_ERROR:
            requirements_file_path = os.path.join(self._output_directory,
                                                  'requirements.txt')
            self._freeze(requirements_file_path)
            with open(requirements_file_path, 'r') as r:
                requirements = r.read()

        if install_result.result_type == PipCheckResultType.SUCCESS:
            install_result = self._check()

        return install_result.with_requirements(requirements)


def check(pip_command: List[str],
          packages: List[str],
          tmp_path: str = None,
          clean: bool = False) -> PipCheckResultType:
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
        tmp_path: The file system path to use for temporary files e.g. "/tmp".
        clean: If True then all previously installed packages will be
            uninstalled before installing "packages".
    """
    return _OneshotPipCheck(pip_command, packages, tmp_path, clean).run()

