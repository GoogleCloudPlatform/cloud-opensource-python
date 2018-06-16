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

import compatibility_checker
import compatibility_store
import package

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


def write_to_status_table():
    # Write self compatibility status to BigQuery
    for py_version in [PY2, PY3]:
        results = checker.get_self_compatibility(py_version)
        res_list = _result_dict_to_compatibility_result(results, py_version)
        store.save_compatibility_statuses(res_list)

    # Write pairwise compatibility status to BigQuery
    for py_version in [PY2, PY3]:
        results = checker.get_pairwise_compatibility(py_version)
        res_list = _result_dict_to_compatibility_result(results, py_version)
        store.save_compatibility_statuses(res_list)


if __name__ == '__main__':
    write_to_status_table()
