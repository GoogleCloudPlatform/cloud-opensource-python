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

from typing import Iterable, List

from compatibility_lib import package
from compatibility_lib import compatibility_store


class CompatibilityStore:
    """Storage for package compatibility information."""

    def __init__(self):
        self._packages_to_compatibility_result = {}

    def _x(self, packages):
        return frozenset(p.install_name for p in packages)

    def get_packages(self) -> Iterable[package.Package]:
        """Returns all packages tracked by the system."""

        return [p[0]
                for p in self._packages_to_compatibility_result.keys()
                if len(p) == 1]

    def get_self_compatibility(self,
                               p: package.Package) -> \
            Iterable[compatibility_store.CompatibilityResult]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            p: The package to check internal compatibility for.

        Yields:
            One CompatibilityResult per Python version.
        """
        return self._packages_to_compatibility_result.get(self._x([p]), [])

    def get_pair_compatibility(self, packages: List[package.Package]) -> \
            Iterable[compatibility_store.CompatibilityResult]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            packages: The packages to check compatibility for.

        Yields:
            One CompatibilityResult per Python version.
        """
        return self._packages_to_compatibility_result.get(self._x(packages),
                                                          [])

    def save_compatibility_statuses(
            self,
            compatibility_statuses: Iterable[
                compatibility_store.CompatibilityResult]):
        """Save the given CompatibilityStatuses"""

        for cr in compatibility_statuses:
            self._packages_to_compatibility_result.setdefault(
                self._x(cr.packages), []).append(cr)
