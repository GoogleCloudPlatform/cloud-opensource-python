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
import retrying
from typing import Any, FrozenSet, Iterable, List, Mapping, Optional

from google.cloud import bigquery
from google.cloud.bigquery import table

from compatibility_lib import package

_DATASET_NAME = 'compatibility_checker'
_SELF_COMPATIBILITY_STATUS_TABLE_NAME = 'self_compatibility_status'
_PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME = 'pairwise_compatibility_status'
_RELEASE_TIME_FOR_DEPENDENCIES_TABLE_NAME = 'release_time_for_dependencies'


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
        dependency_info: The dict contains the dependency version info and
            release time info.
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
        return ('CompatibilityResult({}, {}, {}, {}, {}, {})'.format(
            self.packages, self.python_major_version, self.status,
            self.details, self.timestamp, self.dependency_info))

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

    def __init__(self, project_id=None):
        self._client = bigquery.Client(project=project_id)
        dataset_ref = self._client.dataset(_DATASET_NAME)

        self._self_table_id = (
            '{}.{}'.format(
                _DATASET_NAME, _SELF_COMPATIBILITY_STATUS_TABLE_NAME))
        self._self_table = self._client.get_table(dataset_ref.table(
            _SELF_COMPATIBILITY_STATUS_TABLE_NAME))

        self._pairwise_table_id = (
            '{}.{}'.format(
                _DATASET_NAME, _PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME))
        self._pairwise_table = self._client.get_table(dataset_ref.table(
            _PAIRWISE_COMPATIBILITY_STATUS_TABLE_NAME))

        self._release_time_table_id = (
            '{}.{}'.format(
                _DATASET_NAME, _RELEASE_TIME_FOR_DEPENDENCIES_TABLE_NAME))
        self._release_time_table = self._client.get_table(dataset_ref.table(
            _RELEASE_TIME_FOR_DEPENDENCIES_TABLE_NAME))

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
    def _compatibility_status_to_release_time_row(
            cs: CompatibilityResult) -> List[Mapping[str, Any]]:
        """Converts a CompatibilityResult into a dict which is a row for
        release time table."""
        if len(cs.packages) != 1 or cs.dependency_info is None:
            return []
        install_name = cs.packages[0].install_name
        dependency_info = cs.dependency_info
        rows = []

        for pkg, version_info in dependency_info.items():
            row = {
                'install_name': install_name,
                'dep_name': pkg,
            }
            row.update(version_info)
            row['timestamp'] = row.pop('current_time')
            rows.append(row)

        return rows

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
        query = 'SELECT DISTINCT install_name FROM {}'.format(
            self._self_table_id)
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

    @retrying.retry(stop_max_attempt_number=7,
                    wait_fixed=2000)
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

        query = ('SELECT * '
                 'FROM {} s1 '
                 'WHERE s1.install_name IN UNNEST(@install_names) '
                 '      AND timestamp = ( '
                 '          SELECT MAX(timestamp) '
                 '          FROM {} s2 '
                 '          WHERE s1.install_name = s2.install_name '
                 '            AND s1.py_version = s2.py_version)'.format(
                    self._self_table_id, self._self_table_id))

        query_job = self._client.query(query, job_config=job_config)

        for row in query_job:
            p = install_name_to_package[row.install_name]
            package_to_result[p].append(self._row_to_compatibility_status(
                [p], row))
        return {p: self._filter_older_versions(crs)
                for (p, crs) in package_to_result.items()}

    @retrying.retry(stop_max_attempt_number=7,
                    wait_fixed=2000)
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

        query = ('SELECT * '
                 'FROM {} s1 '
                 'WHERE INSTALL_NAME_LOWER=@install_name_lower '
                 '  AND INSTALL_NAME_HIGHER=@install_name_higher '
                 '  AND timestamp = ( '
                 '     SELECT MAX(timestamp) '
                 '     FROM {} s2 '
                 '     WHERE s1.install_name_lower = s2.install_name_lower '
                 '       AND s1.install_name_higher = s2.install_name_higher '
                 '       AND s1.py_version = s2.py_version)'.format(
                    self._pairwise_table_id, self._pairwise_table_id))
        query_job = self._client.query(query, job_config=job_config)
        return self._filter_older_versions(
            self._row_to_compatibility_status(packages, row)
            for row in query_job)

    @retrying.retry(stop_max_attempt_number=7,
                    wait_fixed=2000)
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

        query = ('SELECT * '
                 'FROM {} s1 '
                 'WHERE s1.install_name_lower IN UNNEST(@install_names) '
                 '  AND s1.install_name_higher IN UNNEST(@install_names) '
                 '  AND timestamp = ( '
                 '     SELECT MAX(timestamp) '
                 '     FROM {} s2 '
                 '     WHERE s1.install_name_lower = s2.install_name_lower '
                 '       AND s1.install_name_higher = s2.install_name_higher '
                 '       AND s1.py_version = s2.py_version)'.format(
                    self._pairwise_table_id, self._pairwise_table_id))

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

        release_time_rows = {}
        for cs in compatibility_statuses:
            if len(cs.packages) == 1:
                install_name = cs.packages[0].install_name
                # Only store the dep info for latest version of the package
                # being checked. e.g. pip install apache-beam will have
                # different version installed in py2/3.
                if not self._should_update_dep_info(
                        cs, release_time_rows.get(install_name)):
                    continue
                row = self._compatibility_status_to_release_time_row(cs)
                if row:
                    release_time_rows[install_name] = row

        for row in release_time_rows.values():
            self._client.insert_rows(
                self._release_time_table,
                row)

    def _should_update_dep_info(self, cs, dep_info_stored):
        """Return True if the stored version is behind latest version."""
        if dep_info_stored is None:
            return True

        install_name = cs.packages[0].install_name
        install_name_sanitized = install_name.split('[')[0] \
            if '[' in install_name else install_name
        installed_version = cs.dependency_info[
            install_name_sanitized]['installed_version']

        installed_version_stored = '0'
        for row in dep_info_stored:
            if row['install_name'] == install_name \
                    and row['dep_name'] == install_name_sanitized:
                installed_version_stored = row['installed_version']
                break

        return True if installed_version > installed_version_stored else False

    @retrying.retry(stop_max_attempt_number=7,
                    wait_fixed=2000)
    def get_dependency_info(self, package_name):
        """Returns dependency info for an indicated Google OSS package.

        Args:
            package_name: The package to lookup for.

        Returns:
            A mapping between the dependency names and the info (dict).
        """
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = []

        tableid = self._release_time_table_id
        query = ('SELECT * '
                 'FROM {0} s1 '
                 'WHERE s1.install_name = "{1}" '
                 'AND timestamp = ( '
                 'SELECT MAX(timestamp) '
                 'FROM {0} s2 '
                 'WHERE s1.install_name = s2.install_name '
                 'AND s1.dep_name = s2.dep_name) '
                 'ORDER BY s1.dep_name'.format(tableid, package_name))

        query_job = self._client.query(query, job_config=job_config)

        dependency_info = {}
        for row in query_job:
            key = row.get('dep_name')
            value = {
                'installed_version': row.get('installed_version'),
                'installed_version_time': row.get('installed_version_time'),
                'latest_version': row.get('latest_version'),
                'latest_version_time': row.get('latest_version_time'),
                'is_latest': row.get('is_latest'),
                'current_time': row.get('timestamp'),
            }
            dependency_info[key] = value

        return dependency_info
