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

"""Common utils methods for badge server."""

import datetime
import enum
import json
import logging
import os
from urllib.parse import urlparse
from urllib.request import urlopen

from typing import Optional

import pybadges

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import dependency_highlighter
from compatibility_lib import deprecated_dep_finder

# Initializations
DB_CONNECTION_NAME = 'python-compatibility-tools:us-central1:' \
                     'compatibility-data'
UNIX_SOCKET = '/cloudsql/{}'.format(DB_CONNECTION_NAME)

checker = compatibility_checker.CompatibilityChecker()
store = compatibility_store.CompatibilityStore(mysql_unix_socket=UNIX_SOCKET)
highlighter = dependency_highlighter.DependencyHighlighter(
    checker=checker, store=store)
finder = deprecated_dep_finder.DeprecatedDepFinder(
    checker=checker, store=store)
priority_level = dependency_highlighter.PriorityLevel

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

URL_PREFIX = 'https://img.shields.io/badge/'
GITHUB_HEAD_NAME = 'github head'
GITHUB_API = 'https://api.github.com/repos'
GITHUB_CACHE_TIME = 1800  # seconds
SVG_CONTENT_TYPE = 'image/svg+xml'
EMPTY_DETAILS = 'NO DETAILS'
PACKAGE_NOT_SUPPORTED = "The package is not supported by checker server."

PY_VER_MAPPING = {
    2: 'py2',
    3: 'py3',
}

STATUS_COLOR_MAPPING = {
    'SUCCESS': 'green',
    'UNKNOWN': 'purple',
    'INSTALL_ERROR': 'yellow',
    'CHECK_WARNING': 'red',
    'CALCULATING': 'blue',
    'CONVERSION_ERROR': 'orange',
    'UP_TO_DATE': 'green',
    'LOW_PRIORITY': 'yellow',
    'HIGH_PRIORITY': 'red',
}

DEFAULT_DEPENDENCY_RESULT = {
    'status': 'CALCULATING',
    'details': {},
}


class BadgeType(enum.Enum):
    """Enum class for badge types."""
    DEP_BADGE = 'dependency_badge'
    SELF_COMP_BADGE = 'self_comp_badge'
    GOOGLE_COMP_BADGE = 'google_comp_badge'


def initialize_cache():
    """Initialize cache based on environment variable."""
    local_cache = 'RUN_LOCALLY'
    redis_cache = 'REDISHOST'

    if os.environ.get(local_cache) is not None:
        import fake_cache
        cache = fake_cache.FakeCache()
    elif os.environ.get(redis_cache) is not None:
        import redis_cache
        cache = redis_cache.RedisCache()
    else:
        import datastore_cache
        cache = datastore_cache.DatastoreCache()

    return cache


def _build_default_result(
        badge_type: BadgeType,
        status: str = 'CALCULATING',
        details: Optional = None) -> dict:
    """Build the default result for different conditions."""
    # Dependency badge
    if badge_type == BadgeType.DEP_BADGE:
        result = {
            'status': status,
            'details': details,
        }
    # Compatibility badge
    else:
        result = {
            'py2': {
                'status': status,
                'details': details,
            },
            'py3': {
                'status': status,
                'details': details,
            }
        }
    return result


def _get_badge(res: dict, badge_name: str) -> str:
    """Generate badge using the check result."""
    if 'github.com' in badge_name:
        badge_name = GITHUB_HEAD_NAME

    status = res.get('status')
    if status is not None:
        # Dependency badge
        color = STATUS_COLOR_MAPPING[status]
    else:
        # Compatibility badge
        status = res['py3']['status']
        if status == 'SUCCESS' and \
            badge_name not in \
                configs.PKG_PY_VERSION_NOT_SUPPORTED.get(2):
            status = res['py2']['status']

        color = STATUS_COLOR_MAPPING[status]

    status = status.replace('_', ' ')
    return pybadges.badge(
        left_text=badge_name,
        right_text=status,
        right_color=color)


def _calculate_commit_number(package: str) -> Optional[str]:
    """Calculate the github head version commit number."""
    url_parsed = urlparse(package)
    if url_parsed.scheme and url_parsed.netloc == 'github.com':
        try:
            owner, repo, *_ = url_parsed.path[1:].split('/')
            repo = repo.split('.git')[0]
        except ValueError:
            return None
        else:
            url = '{0}/{1}/{2}/commits'.format(GITHUB_API, owner, repo)
            try:
                with urlopen(url) as f:
                    commits = json.loads(f.read())
                return commits[0]['sha']
            except Exception as e:
                logging.warning(
                    'Unable to generate caching key for "%s": %s', package, e)
                return None

    return None


def _is_github_cache_valid(cache_timestamp_str=None):
    """Return True if the cached result if calculated within last 30 mins."""
    # Return False if the timestamp str passed in is None
    if cache_timestamp_str is None:
        return False

    cache_timestamp = datetime.datetime.strptime(
        cache_timestamp_str, TIMESTAMP_FORMAT)
    current_timestamp = datetime.datetime.now()
    seconds_diff = (current_timestamp - cache_timestamp).seconds

    if seconds_diff > GITHUB_CACHE_TIME:
        return False
    else:
        return True