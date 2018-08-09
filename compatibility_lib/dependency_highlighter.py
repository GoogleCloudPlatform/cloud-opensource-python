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

from google.cloud import bigquery

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import package
from datetime import datetime

import json
import urllib.request

PY2 = '2'
PY3 = '3'
SERVER_URL = 'http://104.197.8.72'
DATETIME_FORMAT = "%Y-%m-%d"
TABLEID = '`python-compatibility-tools.compatibility_checker.release_time_for_dependencies`'
# TABLEID = 'compatibility_checker.release_time_for_dependencies'
GRACE_PERIOD_IN_DAYS = 30
ALLOWED_MINOR_DIFF = 3

# class PackageDependencies(object):

#     def __init__(self, pkgname, py_version, dependency_info):
#         self.pkgname = pkgname
#         self.py_version = py_version
#         self.dependency_info = dependency_info

#     def __repr__(self):
#         return '{classname}(pkgname={pkgname}, py_version={version})'.format(
#             classname = self.__class__.__name__,
#             pkgname =   self.pkgname,
#             version =   self.py_version)

def _sanitize(release):
    """Handles any pre-release or post-release notation by
    treating them as the previous release (ignores the notation)

    Args:
        release: the semantic release as a string
    Returns:
        a list where each element is an int that represents the
        major, minor, and patch segments preserved in that order
    """
    segments = release.split('.')
    clean_segments = []
    for segment in segments:
        clean_segment = ''
        for c in segment:
            if ord(c) < ord('0') or ord('9') < ord(c):
                break
            clean_segment = '%s%s' % (clean_segment, c)
        clean_segments.append(int(clean_segment))
    return clean_segments


# TODO: consistent truncation
def _parse_datetime(date_string):
    """Converts a date string into a datetime obj

    Args:
        date_string: a date as a string
    Returns:
        the date as a datetime obj
    """
    short_date = date_string.split('T')[0]
    return datetime.strptime(short_date, DATETIME_FORMAT)

# def _get_dependency_info_from_endpoint():
    # APPROACH 1
    # request = '{endpoint}/?package={package}&python-version={version}'.format(
    #     endpoint=SERVER_URL,
    #     package='google-cloud-storage',
    #     version='3')

    # with urllib.request.urlopen(request) as f:
    #     result = json.loads(f.read().decode('utf-8'))

    # return result['dependency_info']

    # APPROACH 2
    # checker = compatibility_checker.CompatibilityChecker()
    # pkg_dependency_lst = []
    # for py_version in [PY2, PY3]:
    #     result = checker.get_self_compatibility(py_version)
    #     for _item in result:
    #         item = _item[0]
    #         if len(item['packages']) > 1:
    #             pkgs = ', '.join(item['packages'])
    #             warn('Expecting "packages" to have 1 entry, got "%s"' % pkgs)
    #         pkgname = item.get('packages')[0]
    #         dependency_info = item.get('dependency_info')
    #         pd = PackageDependencies(pkgname, py_version, dependency_info)
    #         pkg_dependency_lst.append(pd)

    # return pkg_dependency_lst

def _get_dependency_info_from_endpoint(package_name, py_version):
    # APPROACH 3
    checker = compatibility_checker.CompatibilityChecker()
    pkg_dependency_lst = []
    _result = checker.get_dependency_info(package_name, py_version)
    result = [item for item in _result]
    depinfo = result[0][0].get('dependency_info')

    fields = ('installed_version_time', 'current_time', 'latest_version_time')
    for pkgname in depinfo.keys():
        for field in fields:
            depinfo[pkgname][field] = _parse_datetime(depinfo[pkgname][field])

    return depinfo

# TODO: I never used py_version, and I didn't see that as a table column...
def _get_dependency_info_from_bigquery(package_name, py_version):
    client = bigquery.Client()
    job_config = bigquery.QueryJobConfig()
    job_config.query_parameters = []

    query = ('SELECT *'
             'FROM {}'
             'WHERE install_name = "{}"'
             'AND DATE(timestamp) = CURRENT_DATE()'
             'ORDER BY dep_name'.format(TABLEID, package_name))

    query_job = client.query(query, job_config=job_config)
    rows = [row for row in query_job]

    dependency_info = {}
    for row in rows:
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

    # from pdb import set_trace; set_trace()
    return dependency_info

def _find_outdated_dependencies(dependency_info):
    # dependency_info = pkg_dependency.dependency_info
    lowPriority = False
    highPriority = False
    priorities = []
    for name, info in dependency_info.items():
        if not info['is_latest']:
            installed_version = _sanitize(info['installed_version'])
            latest_version =    _sanitize(info['latest_version'])

            # TODO: the time when major version was released
            #       currently, any minor or patch change will extend grace period
            # latest_version_time =   _parse_datetime(info['latest_version_time'])
            # current_time =          _parse_datetime(info['current_time'])
            # elapsed_time =          current_time - latest_version_time
            elapsed_time = info['current_time'] - info['latest_version_time']

            # check for major releases
            if installed_version[0] != latest_version[0]:
                if GRACE_PERIOD_IN_DAYS < elapsed_time.days:
                    highPriority = True
                else:
                    lowPriority = True
                priorities.append('%s Major Version not updated in %s days' % (name, elapsed_time.days))
            # check for minor releases
            elif latest_version[1] - installed_version[1] >= ALLOWED_MINOR_DIFF:
                highPriority = True
                priorities.append('%s Minjor Version behind by %s' % (name, latest_version[1] - installed_version[1]))
            else:
                lowPriority = True
                priorities.append('%s not up to date' % name)
    return priorities


package_name = 'google-cloud-storage'
py_version = '3'
# depinfo1 = _get_dependency_info_from_endpoint(package_name, py_version)
depinfo2 = _get_dependency_info_from_bigquery(package_name, py_version)

priorities = _find_outdated_dependencies(depinfo2)
print('Highlighting outdated dependencies for %s:' % package_name)
for p in priorities:
    print(p)

"""
Plan:
check *CACHE for package dependency info, if N/A...
check BIGQUERY for info, if N/A (should check the configs.PKG_LIST)...
check ENDPOINT for info (endpoint will definitely have the info)
^^^ all logic should go in the badge server eventually ^^^

cache will need to be put off as implementation is not finalized
bigquery -> compatibility_store -> need to add a method to query correct table
endpoint -> compatibility_checker -> need to add a method to get dep info

Issues:
results for endpoint retrieval:
pip Major Version not updated in 18 days
setuptools Major Version not updated in 31 days

results for bigquery retrieval:
pip Major Version not updated in 17 days
setuptools Major Version not updated in 30 days

possible reason:
bigquery will only run at 1am everyday while endpoint is instant(?)

"""