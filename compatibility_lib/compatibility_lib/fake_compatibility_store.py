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

"""In memory storage for package compatibility information."""

import itertools
from typing import Iterable, FrozenSet, List, Mapping

from compatibility_lib import package
from compatibility_lib import compatibility_store
from compatibility_lib import configs


class CompatibilityStore:
    """Storage for package compatibility information."""

    def __init__(self):
        self._packages_to_compatibility_result = {}

    def get_packages(self) -> Iterable[package.Package]:
        """Returns all packages tracked by the system."""

        return [list(p)[0]
                for p in self._packages_to_compatibility_result.keys()
                if len(p) == 1]

    @staticmethod
    def _filter_older_versions(
            crs: Iterable[compatibility_store.CompatibilityResult]) \
            -> Iterable[compatibility_store.CompatibilityResult]:
        """Remove old versions of CompatibilityResults from the given list."""

        def key_func(cr):
            return frozenset(cr.packages), cr.python_major_version

        filtered_results = []
        crs = sorted(crs, key=key_func)
        for _, results in itertools.groupby(crs, key_func):
            filtered_results.append(max(results, key=lambda cr: cr.timestamp))
        return filtered_results

    def get_self_compatibility(self,
                               p: package.Package) -> \
            Iterable[compatibility_store.CompatibilityResult]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            p: The package to check internal compatibility for.

        Yields:
            One CompatibilityResult per Python version.
        """
        return self._filter_older_versions(
            self._packages_to_compatibility_result.get(
                frozenset([p]), []))

    def get_self_compatibilities(self,
                                 packages: Iterable[package.Package]) -> \
            Mapping[package.Package, List[
                compatibility_store.CompatibilityResult]]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            packages: The packages to check internal compatibility for.

        Returns:
            A mapping between the given packages and a (possibly empty)
            list of CompatibilityResults for each one.
        """

        return {p: list(self.get_self_compatibility(p)) for p in packages}

    def get_pair_compatibility(self, packages: List[package.Package]) -> \
            Iterable[compatibility_store.CompatibilityResult]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            packages: The packages to check compatibility for.

        Yields:
            One CompatibilityResult per Python version.
        """
        return self._filter_older_versions(
            self._packages_to_compatibility_result.get(
                frozenset(packages),
                []))

    def get_pairwise_compatibility_for_package(self, package_name: str) -> \
            Mapping[FrozenSet[package.Package],
                    List[compatibility_store.CompatibilityResult]]:
        """Returns a mapping between package pairs and CompatibilityResults.

        Args:
            package_name: The package to check compatibility for.

        Returns:
            A mapping between every pairing between the given package with
            each google cloud python package (found in configs.PKG_LIST) and
            their pairwise CompatibilityResults. For example:
            Given package_name = 'p1', configs.PKG_LIST = [p2, p3, p4] =>
            {
               frozenset([p1, p2]): [CompatibilityResult...],
               frozenset([p1, p3]): [CompatibilityResult...],
               frozenset([p1, p4]): [CompatibilityResult...],
            }.
        """
        package_pairs = [[package.Package(package_name), package.Package(name)]
                         for name in configs.PKG_LIST]
        results = {frozenset(pair): self.get_pair_compatibility(pair)
                   for pair in package_pairs}
        return results


    def get_compatibility_combinations(self,
                                       packages: List[package.Package]) -> \
            Mapping[FrozenSet[package.Package], List[
                compatibility_store.CompatibilityResult]]:
        """Returns a mapping between package pairs and CompatibilityResults.

        Args:
            packages: The packages to check compatibility for.

        Returns:
            A mapping between every combination of input packages and their
            CompatibilityResults. For example:
            get_compatibility_combinations(packages = [p1, p2, p3]) =>
            {
               frozenset([p1, p2]): [CompatibilityResult...],
               frozenset([p1, p3]): [CompatibilityResult...],
               frozenset([p2, p3]): [CompatibilityResult...],
            }.
        """
        return {frozenset([p1, p2]): self.get_pair_compatibility([p1, p2])
                for (p1, p2) in itertools.combinations(packages, r=2)}

    def save_compatibility_statuses(
            self,
            compatibility_statuses: Iterable[
                compatibility_store.CompatibilityResult]):
        """Save the given CompatibilityStatuses"""

        for cr in compatibility_statuses:
            self._packages_to_compatibility_result.setdefault(
                frozenset(cr.packages), []).append(cr)

    def get_dependency_info(self, package_name):
        dep_info = {
            "dep1": {
                "installed_version": '0.1.0',
                "installed_version_time": "2017-02-01 19:15:09+00:00",
                "latest_version": "0.2.8.2",
                "latest_version_time": "2018-06-22 22:12:44+00:00",
                "is_latest": "false",
                "current_time": "2018-08-16 01:08:59.193692+00:00"
            },
            "dep2": {
                "installed_version": "1.0.2",
                "installed_version_time": "2016-04-25 22:22:05+00:00",
                "latest_version": "1.0.2",
                "latest_version_time": "2016-04-25 22:22:05+00:00",
                "is_latest": "true",
                "current_time": "2018-08-16 01:08:59.490506+00:00"
            },
            "dep3": {
                "installed_version": "0.16.0",
                "installed_version_time": "2016-10-27 20:07:22+00:00",
                "latest_version": "0.16.0",
                "latest_version_time": "2016-10-27 20:07:22+00:00",
                "is_latest": "true",
                "current_time": "2018-08-16 01:08:59.554068+00:00"
            },
        }
        return dep_info
