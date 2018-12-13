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

import enum
import os
from typing import Optional

import pybadges

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import dependency_highlighter
from compatibility_lib import deprecated_dep_finder

# Initializations
checker = compatibility_checker.CompatibilityChecker()
store = compatibility_store.CompatibilityStore()
highlighter = dependency_highlighter.DependencyHighlighter(
    checker=checker, store=store)
finder = deprecated_dep_finder.DeprecatedDepFinder(
    checker=checker, store=store)
priority_level = dependency_highlighter.PriorityLevel

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

URL_PREFIX = 'https://img.shields.io/badge/'
GITHUB_HEAD_NAME = 'github head'
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
