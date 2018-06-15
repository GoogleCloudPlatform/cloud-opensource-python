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

"""Represents a pip-installable Python package."""

from typing import Optional


class Package:
    """A pip-installable Python package.

    Attributes:
        installed_name: The name that would be used in the "pip install"
            command e.g. "tensorflow" or
            "git+git://github.com/apache/beam#subdirectory=sdks/python".
        friendly_name: The friendly name of the package e.g. "tensorflow"
            or "apache_beam (git HEAD)"
    """

    def __init__(self, install_name: str, friendly_name: Optional[str] = None):
        """Initializer for Package.

        Args:
            install_name: The name that would be used in the "pip install"
                command e.g. "tensorflow" or
                "git+git://github.com/apache/beam#subdirectory=sdks/python".
            friendly_name: The friendly name of the package e.g. "tensorflow"
                or "apache_beam (git HEAD)"
        """
        self._install_name = install_name
        self._friendly_name = friendly_name or install_name

    def __repr__(self):
        return f'Package({self.install_name})'

    @property
    def install_name(self) -> str:
        return self._install_name

    @property
    def friendly_name(self) -> str:
        return self._friendly_name
