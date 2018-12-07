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

import datetime

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import package

checker = compatibility_checker.CompatibilityChecker()
store = compatibility_store.CompatibilityStore()

PY2 = '2'
PY3 = '3'


def _result_dict_to_compatibility_result(results, python_version):
    res_list = []

    for item in results:
        res_dict = item[0]
        check_result = res_dict.get('result')
        packages_list = [package.Package(pkg)
                         for pkg in res_dict.get('packages')]
        details = res_dict.get('description')
        timestamp = datetime.datetime.now().isoformat()
        dependency_info = res_dict.get('dependency_info')

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


def _generate_pairs_for_github_head():
    """Generate pairs for each github head package with the PyPI packages.
    
    e.g. [(github_pkg, pkg1), (github_pkg, pkg2),...]
    """
    pkg_pairs = []

    for gh_pkg in configs.WHITELIST_URLS.keys():
        gh_pairs = [(gh_pkg, package) for package in configs.PKG_LIST]
        pkg_pairs.extend(gh_pairs)

    return pkg_pairs


def write_to_status_table():
    """Get the compatibility status for PyPI and github head versions."""
    # Write self compatibility status to BigQuery
    self_res_list = []
    packages = configs.PKG_LIST + list(configs.WHITELIST_URLS.keys())
    for py_version in [PY2, PY3]:
        results = checker.get_self_compatibility(
            python_version=py_version,
            packages=packages)
        res_list = _result_dict_to_compatibility_result(results, py_version)
        self_res_list.extend(res_list)

    print(self_res_list)

    # store.save_compatibility_statuses(self_res_list)

    # Write pairwise compatibility status to BigQuery
    for py_version in [PY2, PY3]:
        # For PyPI released versions
        results = checker.get_pairwise_compatibility(py_version)
        res_list = _result_dict_to_compatibility_result(results, py_version)
        # store.save_compatibility_statuses(res_list)

        # For github head versions
        pkg_sets = _generate_pairs_for_github_head()
        results = checker.get_pairwise_compatibility(
            python_version=py_version,
            pkg_sets=pkg_sets)
        res_list = _result_dict_to_compatibility_result(results, py_version)
        print(res_list)
        # store.save_compatibility_statuses(res_list)


if __name__ == '__main__':
    write_to_status_table()
