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

import concurrent.futures
import enum
import logging
import re

from compatibility_lib import compatibility_checker
from compatibility_lib import configs
from compatibility_lib import utils

DEFAULT_GRACE_PERIOD_IN_DAYS = 183  # applies to any version updates
MAJOR_GRACE_PERIOD_IN_DAYS = 30     # applies to major version updates only
ALLOWED_MINOR_DIFF = 3


class UnstableReleaseError(Exception):
    pass


class PriorityLevel(enum.Enum):
    UP_TO_DATE = 0
    LOW_PRIORITY = 1
    HIGH_PRIORITY = 2


class Priority(object):
    """Representation of an update priority"""

    def __init__(self, level=None, details=None):
        if level is None:
            level = PriorityLevel.UP_TO_DATE
        if details is None:
            details = ""
        self.level = level
        self.details = details


class OutdatedDependency(object):
    """Representation of an outdated dependency"""

    def __init__(self, pkgname, parent, priority, info):
        self.name = pkgname
        self.parent = parent
        self.priority = priority

        self.installed_version = info['installed_version']
        self.installed_version_time = info['installed_version_time']
        self.latest_version = info['latest_version']
        self.latest_version_time = info['latest_version_time']
        self.current_time = info['current_time']

    def __repr__(self):
        return ('OutdatedDependency<\'{}\', {}>'.format(
            self.name, self.priority.level.name))

    def __str__(self):
        msg = ('Dependency Name:\t{}\n'
               'Priority:\t\t{}\n'
               'Installed Version:\t{}\n'
               'Latest Available:\t{}\n'
               'Time Since Latest:\t{} days\n'
               '{}\n')
        return msg.format(
            self.name,
            self.priority.level.name,
            self.installed_version,
            self.latest_version,
            (self.current_time-self.latest_version_time).days,
            self.priority.details)


class DependencyHighlighter(object):
    """Highlights outdated dependencies"""

    def __init__(self, py_version=None, checker=None, store=None):
        if py_version is None:
            py_version = '3'

        if checker is None:
            checker = compatibility_checker.CompatibilityChecker()

        self.py_version = py_version
        self._checker = checker
        self._store = store
        self._dependency_info_getter = utils.DependencyInfo(
            py_version, self._checker, self._store)

    def _get_update_priority(self, depname, install, latest, elapsed_time):
        """Returns the update priority level for an outdated dependency

        Args:
            install: the version the package depends on (dict)
            latest: the latest version of a package (dict)
            elapsed_time: time between the latest version release date
                and the install version release date (date.timedelta)
        Returns:
            the priority level and reason explanation
        """
        if install['major'] != latest['major']:
            msg = ('%s is 1 or more major versions '
                   'behind the latest version' % depname)
            if latest['major'] - install['major'] > 1:
                return Priority(PriorityLevel.HIGH_PRIORITY, msg)

            if latest['minor'] > 0 or latest['patch'] > 0:
                return Priority(PriorityLevel.HIGH_PRIORITY, msg)

            msg = ('it has been over 30 days since the major version '
                   'for %s was released' % depname)
            if MAJOR_GRACE_PERIOD_IN_DAYS < elapsed_time.days:
                return Priority(PriorityLevel.HIGH_PRIORITY, msg)

        if ALLOWED_MINOR_DIFF <= latest['minor'] - install['minor']:
            msg = ('%s is 3 or more minor versions '
                   'behind the latest version' % depname)
            return Priority(PriorityLevel.HIGH_PRIORITY, msg)

        if DEFAULT_GRACE_PERIOD_IN_DAYS < elapsed_time.days:
            msg = ('it has been over 6 months since the latest version '
                   'for %s was released' % depname)
            return Priority(PriorityLevel.HIGH_PRIORITY, msg)

        msg = '%s is not up to date with the latest version' % depname
        return Priority(PriorityLevel.LOW_PRIORITY, msg)

    def check_package(self, package_name):
        """Looks for and returns outdated dependencies for a single package

        Args:
            package_name: the name of the package to query (string)
        Returns:
            a list of outdated dependencies
        """
        dependency_info = self._dependency_info_getter.get_dependency_info(
            package_name)
        outdated_dependencies = []
        for name, info in dependency_info.items():
            if name in configs.IGNORED_DEPENDENCIES:
                continue
            priority = Priority()
            try:
                install = _sanitize_release_tag(info['installed_version'])
            except UnstableReleaseError as err:
                install = None
                priority = Priority(PriorityLevel.HIGH_PRIORITY, str(err))

            if not info['is_latest'] or priority.level != \
                    PriorityLevel.UP_TO_DATE:
                current_time = info['current_time']
                latest_version_time = info['latest_version_time']

                # Skip the check if release timestamp is None.
                if current_time is None or latest_version_time is None:
                    logging.warning(
                        'Release time for dependency {} is not available.'
                        .format(name))
                    continue

                try:
                    latest = _sanitize_release_tag(info['latest_version'])
                except UnstableReleaseError as err:
                    logging.warning(
                        'The latest version of {} is not a stable release.'
                        .format(name))
                    continue

                elapsed_time = current_time - latest_version_time

                if priority.level == PriorityLevel.UP_TO_DATE:
                    priority = self._get_update_priority(
                        name, install, latest, elapsed_time)
                dependency = OutdatedDependency(
                    name, package_name, priority, info)
                outdated_dependencies.append(dependency)
        return outdated_dependencies

    def check_packages(self, packages, max_workers=20):
        """Looks for and returns outdated dependencies for multiple package

        Args:
            packages: a list of package names to query (string)
        Returns:
            a dict mapping dependency name to outdated dependencies
        """
        results = {}
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as p:
            outdated_dependencies = p.map(self.check_package, packages)

            for pkgname, result in zip(packages, outdated_dependencies):
                results[pkgname] = result
        return results


def _sanitize_release_tag(release):
    """Throws an error if the given release version is unstable
    eg. 1.0.dev, 2.1a0, 1.1rc3

    Args:
        release: the semantic release as a string
    Returns:
        a dict that maps the major, minor, and patch (represented as strings)
        to the int value of those fields
    """
    patch_match = r'^\d+\.\d+$'
    match = r'^\d+\.\d+\.\d+$|^\d+\.\d+\.\d+\.\d+$'
    errmsg = ('a dependency cannot have '
              'an unstable release {}'.format(release))
    if re.match(patch_match, release.strip()):
        release = '%s.0' % release
    elif not re.match(match, release.strip()):
        raise UnstableReleaseError(errmsg)
    segments = release.split('.')
    release_info = {
        'major': int(segments[0]),
        'minor': int(segments[1]),
        'patch': int(segments[2])
    }
    return release_info
