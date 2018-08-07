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

# from google.cloud import bigquery

from compatibility_lib import compatibility_store
from compatibility_lib import package
from datetime import datetime

import json
import urllib.request

SERVER_URL = 'http://104.197.8.72'
DATETIME_FORMAT = "%Y-%m-%d"
GRACE_PERIOD_IN_DAYS = 30
ALLOWED_MINOR_DIFF = 3

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

def _parse_datetime(date_string):
    """Converts a date string into a datetime obj

    Args:
        date_string: a date as a string
    Returns:
        the date as a datetime obj
    """
    short_date = date_string.split('T')[0]
    return datetime.strptime(short_date, DATETIME_FORMAT)


request = '{endpoint}/?package={package}&python-version={version}'.format(
    endpoint=SERVER_URL,
    package='google-cloud-storage',
    version='3')

with urllib.request.urlopen(request) as f:
    result = json.loads(f.read().decode('utf-8'))

dependencies = result['dependency_info']

lowPriority = False
highPriority = False
priorities = []
for name, info in dependencies.items():
    if not info['is_latest']:
        installed_version = _sanitize(info['installed_version'])
        latest_version =    _sanitize(info['latest_version'])

        # TODO: the time when major version was released
        #       currently, any minor or patch change will extend grace period
        latest_version_time =   _parse_datetime(info['latest_version_time'])
        current_time =          _parse_datetime(info['current_time'])
        elapsed_time =          current_time - latest_version_time

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

for p in priorities:
    print(p)

# First: run queries against the release_time_for_dependencies table
# p = package.Package('google-cloud-storage')
# store = compatibility_store.CompatibilityStore()
# store.get_self_compatibility(p)
