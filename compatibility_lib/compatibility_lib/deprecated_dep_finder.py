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

import concurrent.futures
import logging

from compatibility_lib import configs
from compatibility_lib import utils

DEPRECATED_STATUS = "Development Status :: 7 - Inactive"


class DeprecatedDepFinder(object):
    """A tool for finding if there are deprecated pacakges in the deps.
    
    This tool looks at the development status field in the package info from
    PyPI JSON API, and if the status if 'Development Status :: 7 - Inactive',
    the package is deprecated.
    """

    def __init__(self, py_version=None, max_workers=10):
        if py_version is None:
            py_version = '3'

        self.max_workers = max_workers
        self.py_version = py_version
        self._dependency_info_getter = utils.DependencyInfo(py_version)

    def _get_development_status_from_pypi(self, package_name):
        """Get the development status for a package.

        All kinds of development statuses:

        Development Status :: 1 - Planning
        Development Status :: 2 - Pre-Alpha
        Development Status :: 3 - Alpha
        Development Status :: 4 - Beta
        Development Status :: 5 - Production/Stable
        Development Status :: 6 - Mature
        Development Status :: 7 - Inactive
        
        Args:
            package_name: the package needs to be checked.
        
        Returns:
            The development status of the package.
        """
        pkg_info = utils.call_pypi_json_api(package_name=package_name)

        try:
            development_status = pkg_info['info']['classifiers'][0]
        except (KeyError, IndexError):
            logging.warning("No development status available.")
            development_status = None

        return development_status

    def get_deprecated_dep(self, package_name):
        """Get deprecated dep for a single package."""
        dependency_info = self._dependency_info_getter.get_dependency_info(
            package_name)
        deprecated_deps = []

        for dep_name in dependency_info:
            development_status = self._get_development_status_from_pypi(
                dep_name)
            if development_status == DEPRECATED_STATUS:
                deprecated_deps.append(dep_name)

        return package_name, deprecated_deps

    def get_deprecated_deps(self, packages=None):
        """Get deprecated deps for all the Google OSS packages."""
        if packages is None:
            packages = configs.PKG_LIST

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            results = p.map(
                self.get_deprecated_dep,
                ((pkg) for pkg in packages))

            for result in zip(results):
                yield result
