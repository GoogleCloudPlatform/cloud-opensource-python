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

from contextlib import closing
import datetime
from distutils import version
import enum
import itertools
import os
from typing import Any, FrozenSet, Iterable, List, Mapping, Optional, Tuple

import pymysql

from compatibility_lib import configs
from compatibility_lib import package

_DATABASE_NAME = 'compatibility_data'
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

    def __init__(self,
                 mysql_user=None,
                 mysql_password=None,
                 mysql_host=None,
                 mysql_port=3306,
                 mysql_unix_socket=None,
                 mysql_db=None):
        if mysql_user is None:
            mysql_user = os.environ.get('MYSQL_USER')
        if mysql_password is None:
            mysql_password = os.environ.get('MYSQL_PASSWORD')
        # Assume using mysql_host to connect if both host and unix_socket
        # are None.
        if mysql_host is None and mysql_unix_socket is None:
            mysql_host = '127.0.0.1'
        if mysql_db is None:
            mysql_db = _DATABASE_NAME

        self.mysql_user = mysql_user
        self.mysql_password = mysql_password
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_unix_socket = mysql_unix_socket
        self.mysql_db = mysql_db

    def connect(self):
        # Assumes that the database is running locally or we are connecting to
        # it through Cloud SQL Proxy if a mysql_host is given. Otherwise
        # connecting using mysql unix socket.
        if self.mysql_unix_socket is not None:
            conn = pymysql.connect(
                unix_socket=self.mysql_unix_socket,
                user=self.mysql_user,
                password=self.mysql_password,
                db=self.mysql_db,
                charset='utf8mb4')
        else:
            conn = pymysql.connect(
                host=self.mysql_host,
                port=self.mysql_port,
                user=self.mysql_user,
                password=self.mysql_password,
                db=self.mysql_db,
                charset='utf8mb4')
        return conn

    @staticmethod
    def _row_to_compatibility_status(packages: Iterable[package.Package],
                                     row: tuple) -> \
            CompatibilityResult:
        """Converts a BigQuery row into a CompatibilityResult."""
        if len(packages) == 1:
            _, status, py_version, timestamp, details = row
        else:
            _, _, status, py_version, timestamp, details = row
        return CompatibilityResult(
            packages,
            python_major_version=int(py_version),
            status=Status(status),
            timestamp=timestamp,
            details=details,
        )

    @staticmethod
    def _compatibility_status_to_row(
            cs: CompatibilityResult) -> Tuple:
        """Converts a CompatibilityResult into a tuple."""
        status = cs.status.value
        py_version = str(cs.python_major_version)
        details = cs.details
        if len(cs.packages) == 1:
            install_name = cs.packages[0].install_name
            return (install_name, status, py_version, None, details)
        else:
            names = sorted([cs.packages[0].install_name,
                            cs.packages[1].install_name])
            install_name_lower, install_name_higher = names
            return (install_name_lower, install_name_higher,
                    status, py_version, None, details)

    @staticmethod
    def _compatibility_status_to_release_time_rows(
            cs: CompatibilityResult) -> List[Tuple]:
        """Converts a CompatibilityResult into a dict which is a row for
        release time table."""
        if len(cs.packages) != 1 or cs.dependency_info is None:
            return []
        install_name = cs.packages[0].install_name
        dependency_info = cs.dependency_info
        rows = []

        for pkg, version_info in dependency_info.items():
            row = (install_name,
                   pkg,
                   version_info['installed_version'],
                   version_info['installed_version_time'],
                   version_info['latest_version'],
                   version_info['latest_version_time'],
                   version_info['is_latest'],
                   version_info['current_time'])
            rows.append(row)

        return rows

    def get_packages(self) -> Iterable[package.Package]:
        """Returns all packages tracked by the system."""
        query = 'SELECT DISTINCT install_name FROM self_compatibility_status'

        with closing(self.connect()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

        for row in results:
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
        packages_list = [p.install_name for p in packages]

        query = ('SELECT * FROM self_compatibility_status WHERE install_name '
                 'IN %s')

        with closing(self.connect()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query, [packages_list])
                results = cursor.fetchall()

        for row in results:
            install_name = row[0]
            p = install_name_to_package[install_name]
            package_to_result[p].append(self._row_to_compatibility_status(
                [p], row))
        return {p: crs for (p, crs) in package_to_result.items()}

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

        query = ("SELECT * FROM pairwise_compatibility_status "
                 "WHERE install_name_lower=%s "
                 "AND install_name_higher=%s")

        with closing(self.connect()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    query,
                    (packages[0].install_name, packages[1].install_name))
                results = cursor.fetchall()

        return [self._row_to_compatibility_status(packages, row)
                for row in results]

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

        install_names = [p.install_name for p in packages]

        query = ('SELECT * FROM pairwise_compatibility_status WHERE '
                 'install_name_lower IN %s AND install_name_higher IN %s')

        with closing(self.connect()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query, (install_names, install_names))
                results = cursor.fetchall()

        for row in results:
            install_name_lower, install_name_higher, _, _, _, _ = row
            p_lower = install_name_to_package[install_name_lower]
            p_higher = install_name_to_package[install_name_higher]
            packages_to_results[frozenset([p_lower, p_higher])].append(
                self._row_to_compatibility_status([p_lower, p_higher], row)
            )
        return {p: crs for (p, crs) in packages_to_results.items()}

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

        self_rows = [r for r in rows if len(r) == 5]
        pair_rows = [r for r in rows if len(r) == 6]

        with closing(self.connect()) as conn:
            with closing(conn.cursor()) as cursor:
                if self_rows:
                    self_sql = ('REPLACE INTO self_compatibility_status '
                                'values (%s, %s, %s, %s, %s)')
                    cursor.executemany(self_sql, self_rows)

                if pair_rows:
                    pair_sql = ('REPLACE INTO pairwise_compatibility_status '
                                'values (%s, %s, %s, %s, %s, %s)')
                    cursor.executemany(pair_sql, pair_rows)

                conn.commit()

        # Dependencies are not stored per Python version. This is not
        # theoretically sound but is probably good enough in practice.
        #
        # If there are multiple compatibility results for the same package,
        # use the dependencies with the highest version for that package.
        # For example, if the following CompatibilityResults were passed to
        # `save_compatibility_statuses`:
        #
        # cr1 = CompatibilityResult(
        #     packages=[Package('package1')],
        #     dependency_info={'package1': {'installed_version': '1.2.3' ...})
        # cr2 = CompatibilityResult(
        #     packages=[Package('package1')],
        #     dependency_info={'package1': {'installed_version': '1.2.4' ...})
        #
        # then the dependency information for `cr2` would be saved because it
        # is the newest version ('1.2.4' vs '1.2.3'). If the versions are the
        # same then choose one arbitrarily.
        #
        # This check is done to prevent an old versions of apache-beam, which
        # was accidentally released for Python 3, from having it's dependencies
        # stored. It will also make sure that the Python 3 version of package
        # dependencies are stored when Python 2 releases stop happening.
        install_name_to_compatibility_result = {}
        for cs in compatibility_statuses:
            if len(cs.packages) == 1:
                install_name = cs.packages[0].install_name
                if install_name not in install_name_to_compatibility_result:
                    install_name_to_compatibility_result[install_name] = cs
                else:
                    old_version_string = self._get_package_version(
                        install_name_to_compatibility_result[install_name])
                    new_version_string = self._get_package_version(cs)

                    old_version = version.LooseVersion(old_version_string)
                    new_version = version.LooseVersion(new_version_string)
                    if new_version > old_version:
                        install_name_to_compatibility_result[install_name] = cs

        dependency_rows = itertools.chain(
            *[self._compatibility_status_to_release_time_rows(cs)
              for cs in install_name_to_compatibility_result.values()])

        # Insert the dependency rows in a stable order to make testing more
        # convenient.
        dependency_rows = sorted(
            dependency_rows,
            key=lambda row: (row[0], row[1]))  # install_name, dep_name

        if dependency_rows:
            sql = ('REPLACE INTO release_time_for_dependencies values '
                   '(%s, %s, %s, %s, %s, %s, %s, %s)')

            with closing(self.connect()) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.executemany(sql, dependency_rows)
                    conn.commit()

    def _get_package_version(self, result: CompatibilityResult) -> str:
        """Returns the version of the single package in a CompatibilityResult.

        Args:
            result: The compatibility result. This result must contain exactly
                one package.

        Returns:
            A string containing the version of the single package found in the
            CompatibilityResult `packages` attribute. For example:

            cr1 = CompatibilityResult(
                packages=[Package('package1')],
                dependency_info={'package1': {'installed_version': '1.2.3' ..})
            _get_package_version(cr1) => '1.2.3'
        """
        if len(result.packages) != 1:
            raise ValueError('multiple packages found in CompatibilityResult')

        install_name = result.packages[0].install_name
        if 'github.com' in install_name:
            install_name = configs.WHITELIST_URLS[install_name]
        install_name_sanitized = install_name.split('[')[0]
        print(install_name_sanitized)

        for pkg, version_info in result.dependency_info.items():
            if pkg == install_name_sanitized:
                return version_info['installed_version']
        raise ValueError('missing version information for {}'.format(
            install_name_sanitized))

    def get_dependency_info(self, package_name):
        """Returns dependency info for an indicated Google OSS package.

        Args:
            package_name: The package to lookup for.

        Returns:
            A mapping between the dependency names and the info (dict).
        """
        query = ("SELECT * FROM release_time_for_dependencies "
                 "WHERE install_name=%s")

        with closing(self.connect()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query, package_name)
                results = cursor.fetchall()

        dependency_info = {}
        for row in results:
            install_name, dep_name, installed_version,\
                installed_version_time, latest_version,\
                latest_version_time, is_latest, timestamp = row
            key = dep_name
            value = {
                'installed_version': installed_version,
                'installed_version_time': installed_version_time,
                'latest_version': latest_version,
                'latest_version_time': latest_version_time,
                'is_latest': is_latest,
                'current_time': timestamp,
            }
            dependency_info[key] = value

        return dependency_info
