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

"""Get self and pairwise compatibility data and write to bigquery."""

import argparse
import datetime
import itertools

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import package

checker = compatibility_checker.CompatibilityChecker(max_workers=800)
store = compatibility_store.CompatibilityStore()

PY2 = '2'
PY3 = '3'


def _result_dict_to_compatibility_result(results):
    res_list = []

    for item in results:
        res_dict = item[0]
        result_content, python_version = res_dict
        check_result = result_content.get('result')
        packages_list = [package.Package(pkg)
                         for pkg in result_content.get('packages')]
        details = result_content.get('description')
        timestamp = datetime.datetime.now().isoformat()
        dependency_info = result_content.get('dependency_info')

        compatibility_result = compatibility_store.CompatibilityResult(
            packages=packages_list,
            python_major_version=python_version,
            status=compatibility_store.Status(check_result),
            details=details,
            timestamp=timestamp,
            dependency_info=dependency_info
        )
        res_list.append(compatibility_result)

    return res_list


def get_package_pairs(check_pypi=False, check_github=False):
    """Get package pairs for pypi and github head."""
    self_packages = []
    pair_packages = []
    if check_pypi:
        # Get pypi packages for single checks
        self_packages.extend(configs.PKG_LIST)
        # Get pypi packages for pairwise checks
        pypi_pairs = list(itertools.combinations(configs.PKG_LIST, 2))
        pair_packages.extend(pypi_pairs)
    if check_github:
        # Get github head packages for single checks
        self_packages.extend(list(configs.WHITELIST_URLS.keys()))
        # Get github head packages for pairwise checks
        for gh_url in configs.WHITELIST_URLS:
            pairs = []
            gh_name = configs.WHITELIST_URLS[gh_url]
            for pypi_pkg in configs.PKG_LIST:
                if pypi_pkg != gh_name:
                    pairs.append((gh_url, pypi_pkg))
            pair_packages.extend(pairs)

    return self_packages, pair_packages


def write_to_status_table(check_pypi=False, check_github=False):
    """Get the compatibility status for PyPI versions."""
    # Write self compatibility status to BigQuery
    self_packages, pair_packages = get_package_pairs(check_pypi, check_github)
    results = checker.get_compatibility(
        packages=self_packages, pkg_sets=pair_packages)
    res_list = _result_dict_to_compatibility_result(results)

    store.save_compatibility_statuses(res_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Determine what to check.')
    parser.add_argument(
        '--pypi',
        type=bool,
        default=False,
        help='Check PyPI released packages or not.')
    parser.add_argument(
        '--github',
        type=bool,
        default=False,
        help='Check GitHub head packages or not.')
    args = parser.parse_args()

    check_pypi = args.pypi
    check_github = args.github
    write_to_status_table(check_pypi, check_github)
