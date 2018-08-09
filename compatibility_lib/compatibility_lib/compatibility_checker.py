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
import urllib.request
import json
import retrying

from compatibility_lib import configs

SERVER_URL = 'http://104.197.8.72'


class CompatibilityChecker(object):

    def __init__(self, max_workers=20):
        self.max_workers = max_workers

    def check(self, packages, python_version):
        """Call the checker server to get back status results."""
        data = json.dumps({
            'python-version': python_version,
            'packages': packages
        }).encode('utf-8')

        check_request = urllib.request.Request(SERVER_URL, data)

        with urllib.request.urlopen(check_request) as f:
            result = json.loads(f.read().decode('utf-8'))

        return result

    @retrying.retry(wait_exponential_multiplier=5000,
                    wait_exponential_max=20000)
    def retrying_check(self, args):
        """Retrying logic for sending requests to checker server."""
        packages = args[0]
        python_version = args[1]
        return self.check(packages, python_version)

    def get_self_compatibility(self, python_version):
        """Get the self compatibility data for each package."""
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            pkg_set_results = p.map(
                self.retrying_check,
                (([pkg], python_version) for pkg in configs.PKG_LIST))

            for result in zip(pkg_set_results):
                yield result

    def get_pairwise_compatibility(self, python_version):
        """Get pairwise compatibility data for each pair of packages."""
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            pkg_sets = itertools.combinations(configs.PKG_LIST, 2)
            pkg_set_results = p.map(
                self.retrying_check,
                ((list(pkg_set), python_version) for pkg_set in pkg_sets))

            for result in zip(pkg_set_results):
                yield result

    # TODO: delete this method and refactor get_self_compatibility
    def get_dependency_info(self, package_name, python_version):
        """Get the self compatibility data for each package."""
        pkgs = [package_name]
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as p:
            pkg_set_results = p.map(
                self.retrying_check,
                (([pkg], python_version) for pkg in pkgs))

            for result in zip(pkg_set_results):
                yield result
