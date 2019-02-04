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
import concurrent.futures
import json
import requests
import retrying

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

        data = {
            'python-version': python_version,
            'package': packages
        }
        result = requests.get(SERVER_URL, params=data)
        content = result.content.decode('utf-8')

        return json.loads(content)

    def filter_packages(self, packages, python_version):
        return [pkg for pkg in packages if pkg not in
                configs.PKG_PY_VERSION_NOT_SUPPORTED[int(python_version)]]

    @retrying.retry(wait_exponential_multiplier=5000,
                    wait_exponential_max=20000)
    def retrying_check(self, args):
        """Retrying logic for sending requests to checker server."""
        packages = args[0]
        python_version = args[1]
        return self.check(packages, python_version)

    def get_self_compatibility(self, python_version, packages=None):
        """Get the self compatibility data for each package."""
        if packages is None:
            packages = configs.PKG_LIST
            # Remove the package not supported in the python_version
            packages = self.filter_packages(packages, python_version)
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            pkg_set_results = p.map(
                self.retrying_check,
                (([pkg], python_version) for pkg in packages))

            for result in zip(pkg_set_results):
                yield result

    def get_pairwise_compatibility(self, python_version, pkg_sets=None):
        """Get pairwise compatibility data for each pair of packages."""
        if pkg_sets is None:
            packages = self.filter_packages(configs.PKG_LIST, python_version)
            pkg_sets = itertools.combinations(packages, 2)
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            pkg_set_results = p.map(
                self.retrying_check,
                ((list(pkg_set), python_version) for pkg_set in pkg_sets))

            for result in zip(pkg_set_results):
                yield result
