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

"""Storage for package compatibility information."""

import datetime
import enum
import itertools
from typing import Any, FrozenSet, Iterable, List, Mapping, Optional

from google.cloud import bigquery
from google.cloud.bigquery import table

from compatibility_lib import package

_DATASET_NAME = 'compatibility_checker'
_SELF_COMPATIBILITY_STATUS_TABLE_NAME = 'self_compatibility_status'
_PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME = 'pairwise_compatibility_status'


class Status(enum.Enum):
    UNKNOWN = "UNKNOWN"
    SUCCESS = "SUCCESS"
    INSTALL_ERROR = "INSTALL_ERROR"
    CHECK_WARNING = "CHECK_WARNING"


class CompatibilityResult:
    """The result of checking the compatibility between packages.

    Attributes:
        packages: The list of packages there were checked for compatibility.
        python_major_version: The major Python version used for the
            compatibility check i.e. 2 or 3.
        status: The overall result of the compatibility check.
        details: A text description of the compatibility check. Will be None
            if the check succeeded.
        timestamp: The time at which the compatibility check was performed.
    """

    def __init__(self,
                 packages: Iterable[package.Package],
                 python_major_version: int,
                 status: Status = Status.UNKNOWN,
                 details: Optional[str] = None,
                 dependency_info: Optional[Mapping[str, Any]] = None,
                 timestamp: Optional[datetime.datetime] = None):
        self._packages = list(packages)
        self._python_major_version = python_major_version
        self._status = status
        self._details = details
        self._dependency_info = dependency_info
        if timestamp:
            self._timestamp = timestamp
        else:
            self._timestamp = datetime.datetime.now(datetime.timezone.utc)

    def __repr__(self):
        return (f'CompatibilityResult({self.packages}, '
                f'{self.python_major_version}, {self.status}, {self.details}, '
                f'{self.timestamp}, '
                f'{self.dependency_info})')

    def __hash__(self):
        return hash((tuple(self.packages), self.status, self.timestamp))

    def __eq__(self, o):
        if isinstance(o, CompatibilityResult):
            return (frozenset(self.packages) == frozenset(o.packages) and
                    self.python_major_version == o.python_major_version and
                    self.status == o.status and
                    self.details == o.details and
                    self.dependency_info == o.dependency_info and
                    self.timestamp == o.timestamp)
        return NotImplemented

    @property
    def packages(self) -> List[package.Package]:
        return self._packages

    @property
    def python_major_version(self) -> int:
        return self._python_major_version

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, status: Status):
        self._status = status

    @property
    def details(self) -> Optional[str]:
        return self._details

    @property
    def dependency_info(self) -> Optional[Mapping[str, Any]]:
        return self._dependency_info

    @property
    def timestamp(self) -> datetime.datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime.datetime):
        self._timestamp = timestamp


class CompatibilityStore:
    """Storage for package compatibility information."""

    def __init__(self):
        self._client = bigquery.Client()
        dataset_ref = self._client.dataset(_DATASET_NAME)

        self._self_table_id = (
            f'{_DATASET_NAME}.{_SELF_COMPATIBILITY_STATUS_TABLE_NAME}')
        self._self_table = self._client.get_table(dataset_ref.table(
            _SELF_COMPATIBILITY_STATUS_TABLE_NAME))

        self._pairwise_table_id = (
            f'{_DATASET_NAME}.{_PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME}')
        self._pairwise_table = self._client.get_table(dataset_ref.table(
            _PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME))

    @staticmethod
    def _row_to_compatibility_status(packages: Iterable[package.Package],
                                     row: table.Row) -> \
            CompatibilityResult:
        """Converts a BigQuery row into a CompatibilityResult."""
        return CompatibilityResult(
            packages,
            python_major_version=int(row.py_version[0]),
            status=Status(row.status),
            timestamp=row.timestamp,
            details=row.details,
        )

    @staticmethod
    def _compatibility_status_to_row(
            cs: CompatibilityResult) -> Mapping[str, Any]:
        """Converts a CompatibilityResult into a dict whose keys are columns.
        """
        row = {
            'status': cs.status.value,
            'py_version': str(cs.python_major_version),
            'timestamp': cs.timestamp,
            'details': cs.details,
        }
        if len(cs.packages) == 1:
            row['install_name'] = cs.packages[0].install_name
        else:
            names = sorted([cs.packages[0].install_name,
                            cs.packages[1].install_name])
            row['install_name_lower'], row['install_name_higher'] = names
        return row

    @staticmethod
    def _filter_older_versions(crs: Iterable[CompatibilityResult]) \
            -> Iterable[CompatibilityResult]:
        """Remove old versions of CompatibilityResults from the given list."""

        def key_func(cr):
            return frozenset(cr.packages), cr.python_major_version

        filtered_results = []
        crs = sorted(crs, key=key_func)
        for _, results in itertools.groupby(crs, key_func):
            filtered_results.append(max(results, key=lambda cr: cr.timestamp))
        return filtered_results

    def get_packages(self) -> Iterable[package.Package]:
        """Returns all packages tracked by the system."""
        query = f'SELECT DISTINCT install_name FROM {self._self_table_id}'
        query_job = self._client.query(query)
        for row in query_job:
            yield package.Package(install_name=row[0])

    def get_self_compatibility(self,
                               p: package.Package) -> \
            Iterable[CompatibilityResult]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            p: The package to check internal compatibility for.

        Yields:
            One CompatibilityResult per Python version.
        """
        return self.get_self_compatibilities([p])[p]

    def get_self_compatibilities(self,
                                 packages: Iterable[package.Package]) -> \
            Mapping[package.Package, List[CompatibilityResult]]:
        """Returns CompatibilityStatuses for internal package compatibility.

        Args:
            packages: The packages to check internal compatibility for.

        Returns:
            A mapping between the given packages and a (possibly empty)
            list of CompatibilityResults for each one.
        """

        install_name_to_package = {p.install_name: p for p in packages}
        package_to_result = {p: [] for p in packages}

        query_params = [
            bigquery.ArrayQueryParameter('install_names', 'STRING',
                                         [package.install_name
                                          for package in packages]),
        ]
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = query_params

        query = (f'SELECT * '
                 f'FROM {self._self_table_id} s1 '
                 f'WHERE s1.install_name IN UNNEST(@install_names) '
                 f'      AND timestamp = ( '
                 f'          SELECT MAX(timestamp) '
                 f'          FROM {self._self_table_id} s2 '
                 f'          WHERE s1.install_name = s2.install_name '
                 f'            AND s1.py_version = s2.py_version)')

        query_job = self._client.query(query, job_config=job_config)

        for row in query_job:
            p = install_name_to_package[row.install_name]
            package_to_result[p].append(self._row_to_compatibility_status(
                [p], row))
        return {p: self._filter_older_versions(crs)
                for (p, crs) in package_to_result.items()}

    def get_pair_compatibility(self, packages: List[package.Package]) -> \
            Iterable[CompatibilityResult]:
        """Returns CompatibilityStatuses for a pair of packages.

        Args:
            packages: The packages to check compatibility for. Must have a
                length of exactly 2.

        Yields:
            One CompatibilityResult per Python version.
        """
        if len(packages) != 2:
            raise ValueError(
                'expected 2 packages, got {}'.format(len(packages)))
        packages = sorted(packages, key=lambda p: p.install_name)
        query_params = [
            bigquery.ScalarQueryParameter('install_name_lower', 'STRING',
                                          packages[0].install_name),
            bigquery.ScalarQueryParameter('install_name_higher', 'STRING',
                                          packages[1].install_name),
        ]
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = query_params

        query = (f'SELECT * '
                 f'FROM {self._pairwise_table_id} s1 '
                 f'WHERE INSTALL_NAME_LOWER=@install_name_lower '
                 f'  AND INSTALL_NAME_HIGHER=@install_name_higher '
                 f'  AND timestamp = ( '
                 f'     SELECT MAX(timestamp) '
                 f'     FROM {self._pairwise_table_id} s2 '
                 f'     WHERE s1.install_name_lower = s2.install_name_lower '
                 f'       AND s1.install_name_higher = s2.install_name_higher '
                 f'       AND s1.py_version = s2.py_version)')
        query_job = self._client.query(query, job_config=job_config)
        return self._filter_older_versions(
            self._row_to_compatibility_status(packages, row)
            for row in query_job)

    def get_compatibility_combinations(self,
                                       packages: List[package.Package]) -> \
            Mapping[FrozenSet[package.Package], List[CompatibilityResult]]:
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
        install_name_to_package = {p.install_name: p for p in packages}

        packages_to_results = {}
        for p1, p2 in itertools.combinations(packages, r=2):
            packages_to_results[frozenset([p1, p2])] = []

        query_params = [
            bigquery.ArrayQueryParameter('install_names', 'STRING',
                                         [p.install_name for p in packages]),
        ]
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = query_params

        query = (f'SELECT * '
                 f'FROM {self._pairwise_table_id} s1 '
                 f'WHERE s1.install_name_lower IN UNNEST(@install_names) '
                 f'  AND s1.install_name_higher IN UNNEST(@install_names) '
                 f'  AND timestamp = ( '
                 f'     SELECT MAX(timestamp) '
                 f'     FROM {self._pairwise_table_id} s2 '
                 f'     WHERE s1.install_name_lower = s2.install_name_lower '
                 f'       AND s1.install_name_higher = s2.install_name_higher '
                 f'       AND s1.py_version = s2.py_version)')

        query_job = self._client.query(query, job_config=job_config)

        for row in query_job:
            p_lower = install_name_to_package[row.install_name_lower]
            p_higher = install_name_to_package[row.install_name_higher]
            packages_to_results[frozenset([p_lower, p_higher])].append(
                self._row_to_compatibility_status([p_lower, p_higher], row)
            )
        return {p: self._filter_older_versions(crs) for (p, crs) in
                packages_to_results.items()}

    def save_compatibility_statuses(
            self,
            compatibility_statuses: Iterable[
                CompatibilityResult]):
        """Save the given CompatibilityStatuses"""

        compatibility_statuses = list(compatibility_statuses)
        if any(cs for cs in compatibility_statuses
               if len(cs.packages) not in [1, 2]):
            raise ValueError('CompatibilityResult must have 1 or 2 packages')
        rows = [self._compatibility_status_to_row(s) for s in
                compatibility_statuses]
        self_rows = [r for r in rows if 'install_name' in r]
        pair_rows = [r for r in rows if 'install_name' not in r]
        if self_rows:
            self._client.insert_rows(
                self._self_table,
                self_rows)
        if pair_rows:
            self._client.insert_rows(
                self._pairwise_table,
                pair_rows)
