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

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs

from datetime import datetime
import enum

DATETIME_FORMAT = "%Y-%m-%d"
DEFAULT_GRACE_PERIOD_IN_DAYS = 183
MAJOR_GRACE_PERIOD_IN_DAYS = 30
ALLOWED_MINOR_DIFF = 3

class Priority(enum.Enum):
    NONE = "UP_TO_DATE"
    LOW = "LOW_PRIORITY"
    HIGH = "HIGH_PRIORITY"

def _sanitize_release_tag(release):
    """Handles any pre-release or post-release notation by
    treating them as the previous release (ignores the notation)

    Args:
        release: the semantic release as a string
    Returns:
        a list where each element is an int that represents the
        major, minor, and patch segments preserved in that order
    """
    segments = release.split('.')

    release_info = {}
    for i, key in enumerate(('major', 'minor', 'patch')):
        release_info[key] = 0
        if i < len(segments):
            clean_segment = ''
            for c in segments[i]:
                if ord(c) < ord('0') or ord('9') < ord(c):
                    break
                clean_segment = '%s%s' % (clean_segment, c)
            release_info[key] = int(clean_segment)
    return release_info

def _parse_datetime(date_string):
    """Converts a date string into a datetime obj

    Args:
        date_string: a date as a string
    Returns:
        the date as a datetime obj
    """
    short_date = date_string.split('T')[0]
    return datetime.strptime(short_date, DATETIME_FORMAT)

# TODO: implement
def _get_from_cache(package_name, py_version):
    return None

def _get_from_bigquery(package_name):
    if package_name in configs.PKG_LIST:
        store = compatibility_store.CompatibilityStore()
        depinfo = store.get_dependency_info(package_name)
        return depinfo
    else:
        return None

def _get_from_endpoint(package_name, py_version):
    checker = compatibility_checker.CompatibilityChecker()
    depinfo = checker.get_dependency_info(package_name, py_version)

    fields = ('installed_version_time', 'current_time', 'latest_version_time')
    for pkgname in depinfo.keys():
        for field in fields:
            depinfo[pkgname][field] = _parse_datetime(depinfo[pkgname][field])

    return depinfo

def _get_outdated_dependencies(dependency_info):
    lowPriority = False
    highPriority = False
    outdated = []
    for name, info in dependency_info.items():
        info['priority'] = Priority.NONE
        if not info['is_latest']:
            install = _sanitize_release_tag(info['installed_version'])
            latest =  _sanitize_release_tag(info['latest_version'])
            elapsed_time = info['current_time'] - info['latest_version_time']

            priority, msg = _get_update_priority(install, latest, elapsed_time)
            info['priority'] = priority
            outdated.append((name, info, msg))

    return outdated

def _get_update_priority(install, latest, elapsed_time):
    if install['major'] != latest['major']:
        msg = ('it has been over 30 days since the major version '
               'for this dependency was released')
        if latest['major'] - install['major'] > 1:
            return (Priority.HIGH, msg)
        if latest['minor'] > 0 or latest['patch'] > 0:
            return (Priority.HIGH, msg)
        if MAJOR_GRACE_PERIOD_IN_DAYS < elapsed_time.days:
            return (Priority.HIGH, msg)

    if ALLOWED_MINOR_DIFF <= latest['minor'] - install['minor']:
        msg = ('this dependency is 3 or more minor versions '
               'behind the latest version')
        return (Priority.HIGH, msg)

    if DEFAULT_GRACE_PERIOD_IN_DAYS < elapsed_time.days:
        msg = ('it has been over 6 months since the latest version '
               'for this dependency was released')
        return (Priority.HIGH, msg)

    msg = 'this dependency is not up to date with the latest version'
    return (Priority.LOW, msg)

def highlight(package_name, py_version):
    depinfo = _get_from_cache(package_name, py_version)
    if depinfo is None:
        depinfo = _get_from_bigquery(package_name)
    if depinfo is None:
        depinfo = _get_from_endpoint(package_name, py_version)

    outdated = _get_outdated_dependencies(depinfo)

    print('Highlighting {} outdated dependencies for {}:'.format(
        len(outdated), package_name))
    msg = ('Dependency Name:\t{}\n'
           'Priority:\t\t{}\n'
           'Installed Version:\t{}\n'
           'Latest Available:\t{}\n'
           'Time Since Latest:\t{} days\n'
           '{}\n')
    for name, info, reason in outdated:
        print(msg.format(
            name,
            info['priority'].value,
            info['installed_version'],
            info['latest_version'],
            (info['current_time']-info['latest_version_time']).days,
            reason))

if __name__ == '__main__':
    highlight(package_name='google-cloud-storage', py_version='3')
