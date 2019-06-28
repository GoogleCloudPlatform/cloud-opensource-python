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

"""Send request to server to get self and pairwise compatibility data."""

import itertools
import logging
import concurrent.futures
import json
import requests
import retrying
import time

from compatibility_lib import configs
from compatibility_lib import utils

SERVER_URL = 'http://104.197.8.72'

UNKNOWN_STATUS_RESULT = {
    'result': 'UNKNOWN',
}


class CompatibilityChecker(object):

    def __init__(self, max_workers=20):
        self.max_workers = max_workers

    def check(self, packages, python_version):
        """Call the checker server to get back status results."""
        if not utils._is_package_in_whitelist(packages):

            UNKNOWN_STATUS_RESULT['packages'] = packages
            UNKNOWN_STATUS_RESULT['description'] = 'Package is not supported' \
                                                   ' by our checker server.'
            return UNKNOWN_STATUS_RESULT

        start_time = time.time()
        data = {
            'python-version': python_version,
            'package': packages
        }
        # Set the timeout to 299 seconds, which should be less than the
        # docker timeout (300 seconds).
        try:
            result = requests.get(SERVER_URL, params=data, timeout=299)
            content = result.content.decode('utf-8')
        except Exception as e:
            check_time = time.time() - start_time
            logging.getLogger("compatibility_lib").error(
                'Checked {} in {:.1f} seconds: {}'.format(
                    packages, check_time, e))
            raise
        check_time = time.time() - start_time
        logging.getLogger("compatibility_lib").debug(
            'Checked {} in {:.1f} seconds (success!)'.format(
                packages, check_time))
        return json.loads(content), python_version

    def filter_packages(self, packages, python_version):
        """Filter out the packages not supported by the given py version."""
        filtered_packages = []
        for pkg in packages:
            if 'github.com' in pkg:
                pkg_name = configs.WHITELIST_URLS[pkg]
            else:
                pkg_name = pkg
            if pkg_name not in configs.PKG_PY_VERSION_NOT_SUPPORTED[
                    int(python_version)]:
                filtered_packages.append(pkg)
        return filtered_packages

    @retrying.retry(wait_random_min=1000,
                    wait_random_max=2000)
    def retrying_check(self, args):
        """Retrying logic for sending requests to checker server."""
        packages = args[0]
        python_version = args[1]
        return self.check(packages, python_version)

    def collect_check_packages(
            self, python_version=None, packages=None, pkg_sets=None):
        # Generating single packages
        if packages is None:
            packages = configs.PKG_LIST

        check_singles = []
        if python_version is None:
            for py_ver in ['2', '3']:
                # Remove the package not supported in the python_version
                filtered_single = self.filter_packages(packages, py_ver)
                for pkg in filtered_single:
                    check_singles.append(([pkg], py_ver))
        else:
            filtered_single = self.filter_packages(packages, python_version)
            check_singles = [
                ([pkg], python_version) for pkg in filtered_single]

        # Generating pairs
        if pkg_sets is None:
            pkg_sets = list(itertools.combinations(configs.PKG_LIST, 2))

        check_pairs = []
        if python_version is None:
            for py_ver in ['2', '3']:
                filtered_pkgs = []
                for pkgs in pkg_sets:
                    if list(pkgs) != self.filter_packages(pkgs,
                                                          py_ver):
                        continue
                    filtered_pkgs.append(pkgs)
                for pkg_set in filtered_pkgs:
                    check_pairs.append((list(pkg_set), py_ver))
        else:
            filtered_pkgs = []
            for pkgs in pkg_sets:
                if list(pkgs) != self.filter_packages(pkgs,
                                                      python_version):
                    continue
                filtered_pkgs.append(pkgs)
            check_pairs = [(list(pkg_set), python_version)
                           for pkg_set in pkg_sets]

        res = tuple(check_singles) + tuple(check_pairs)
        return res

    def get_compatibility(
            self, python_version=None, packages=None, pkg_sets=None):
        """Get the compatibility data for each package and package pairs."""
        check_packages = self.collect_check_packages(
            python_version, packages, pkg_sets)

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            pkg_set_results = p.map(self.retrying_check, tuple(check_packages))

            for count, result in enumerate(zip(pkg_set_results)):
                if (count and count % self.max_workers == 0 or
                        count == len(check_packages) - 1):
                    logging.getLogger("compatibility_lib").info(
                        "Successfully checked {}/{} in {:.1f}s".format(
                            count, len(check_packages),
                            time.time() - start_time))
                yield result
