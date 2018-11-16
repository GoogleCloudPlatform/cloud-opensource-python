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

"""Common utils for compatibility_lib."""

from datetime import datetime
import json
import logging
import urllib.request

from compatibility_lib import compatibility_checker
from compatibility_lib import configs

DATETIME_FORMAT = "%Y-%m-%d"

PYPI_URL = 'https://pypi.org/pypi/'


class PackageNotSupportedError(Exception):
    """Package is not supported by our checker server."""

    def __init__(self, package_name):
        super(PackageNotSupportedError, self).__init__(
            'Package {} is not supported by our checker server.'.format(
                package_name))
        self.package_name = package_name


def call_pypi_json_api(package_name, pkg_version=None):
    if pkg_version is not None:
        pypi_pkg_url = PYPI_URL + '{}/{}/json'.format(
            package_name, pkg_version)
    else:
        pypi_pkg_url = PYPI_URL + '{}/json'.format(package_name)

    try:
        r = urllib.request.Request(pypi_pkg_url)

        with urllib.request.urlopen(r) as f:
            result = json.loads(f.read().decode('utf-8'))
    except urllib.error.HTTPError:
        logging.error('Package {} with version {} not found in Pypi'.
                      format(package_name, pkg_version))
        return None
    return result


def _is_package_in_whitelist(packages):
    """Return True if all the given packages are in whitelist.

    Args:
        packages: A list of package names.

    Returns:
        True if all packages are in whitelist, else False.
    """
    for pkg in packages:
        if pkg not in configs.PKG_LIST and pkg not in configs.WHITELIST_URLS:
            return False

    return True


class DependencyInfo(object):
    """Common utils of getting dependency info for a package."""

    def __init__(self, py_version=None, checker=None, store=None):
        if py_version is None:
            py_version = '3'

        if checker is None:
            checker = compatibility_checker.CompatibilityChecker()

        self.py_version = py_version
        self.checker = checker
        self.store = store

    def _get_from_bigquery(self, package_name):
        """Gets the package dependency info from bigquery

        Args:
            package_name: the name of the package to query
        Returns:
            a dict mapping from dependency package name (string) to
            the info (dict)
        """
        if self.store is not None and package_name in configs.PKG_LIST:
            depinfo = self.store.get_dependency_info(package_name)
            return depinfo
        else:
            return None

    def _get_from_endpoint(self, package_name):
        """Gets the package dependency info from the compatibility checker
        endpoint.

        Args:
            package_name: the name of the package to query (string)
        Returns:
            a dict mapping from dependency package name (string) to
            the info (dict)
        """
        _result = self.checker.get_self_compatibility(
            self.py_version, [package_name])
        result = [item for item in _result]
        print(result)
        depinfo = result[0][0].get('dependency_info')

        # depinfo can be None if there is an exception during pip install or
        # the package is not supported by checker server (not in whitelist).
        if depinfo is None:
            logging.warning(
                "Could not get the dependency info of package {} from server."
                .format(package_name))
            raise PackageNotSupportedError(package_name)

        fields = ('installed_version_time',
                  'current_time', 'latest_version_time')
        for pkgname in depinfo.keys():
            for field in fields:
                depinfo[pkgname][field] = _parse_datetime(
                    depinfo[pkgname][field])

        return depinfo

    def get_dependency_info(self, package_name):
        """Gets the package dependency info

        Args:
            package_name: the name of the package to query (string)
        Returns:
            a dict mapping from dependency package name (string) to
            the info (dict)
        """
        depinfo = self._get_from_bigquery(package_name)

        if depinfo is None:
            depinfo = self._get_from_endpoint(package_name)
        return depinfo


def _parse_datetime(date_string):
    """Converts a date string into a datetime obj

    Args:
        date_string: a date as a string
    Returns:
        the date as a datetime obj
    """
    if date_string is None:
        return None

    date_string = date_string.replace('T', ' ')
    short_date = date_string.split(' ')[0]
    return datetime.strptime(short_date, DATETIME_FORMAT)
