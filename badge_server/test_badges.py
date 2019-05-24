# Copyright 2019 Google LLC
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
"""Add tests for the badge server image end-point."""

import datetime
import unittest
import unittest.mock
import urllib.parse

from compatibility_lib import compatibility_store
from compatibility_lib import dependency_highlighter
from compatibility_lib import deprecated_dep_finder_stub
from compatibility_lib import fake_compatibility_store
from compatibility_lib import package

import main
import utils

APACHE_BEAM_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('apache-beam[gcp]')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'apache-beam[gcp]': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '2.12.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': True,
            'latest_version': '2.12.0',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/apache-beam.git')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'apache-beam[gcp]': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '2.12.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': True,
            'latest_version': '2.12.0',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.CHECK_WARNING,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_RECENT_INSTALL_FAILURE_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.CHECK_WARNING,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=3,
    status=compatibility_store.Status.CHECK_WARNING,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=2,
    status=compatibility_store.Status.CHECK_WARNING,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=3,
    status=compatibility_store.Status.CHECK_WARNING,
    dependency_info={
        'google-api-core': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.9.0',
            'installed_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
            'is_latest': True,
            'latest_version': '1.9.0',
            'latest_version_time': datetime.datetime(
                2019, 4, 5, 18, 1, 48),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('tensorflow')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'tensorflow': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.3.1',
            'installed_version_time': datetime.datetime(
                2019, 4, 26, 0, 0, 0),
            'is_latest': True,
            'latest_version': '1.3.1',
            'latest_version_time': datetime.datetime(
                2019, 4, 26, 0, 0, 0),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

TENSORFLOW_GIT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/tensorflow.git')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    dependency_info={
        'tensorflow': {
            'current_time': datetime.datetime(2019, 5, 7, 0, 0, 0),
            'installed_version': '1.3.1',
            'installed_version_time': datetime.datetime(
                2019, 4, 26, 0, 0, 0),
            'is_latest': True,
            'latest_version': '1.3.1',
            'latest_version_time': datetime.datetime(
                2019, 4, 26, 0, 0, 0),
        },
    },
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('apache-beam[gcp]'),
     package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3 = compatibility_store.CompatibilityResult(
    [package.Package('apache-beam[gcp]'),
     package.Package('google-api-core')],
    python_major_version=3,   # apache-beam does not support Python 3
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GIT_GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/apache-beam.git'),
     package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/apache-beam.git'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('git+git://github.com/google/api-core.git')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('git+git://github.com/google/api-core.git')
    ],
    python_major_version=3,   # apache-beam does not support Python 3
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('git+git://github.com/google/api-python-client.git')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-core'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-core'),
        package.Package('google-api-python-client')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('google-api-python-client')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core'),
     package.Package('tensorflow')],
    python_major_version=2,   # tensorflow does not support Python 2
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core'),
     package.Package('tensorflow')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('tensorflow')
    ],
    python_major_version=2,   # tensorflow does not support Python 2
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('tensorflow')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

GOOGLE_API_PYTHON_CLIENT_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-python-client'),
        package.Package('tensorflow')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime(2019, 5, 7, 0, 0, 0))

RECENT_SUCCESS_DATA = [
    APACHE_BEAM_RECENT_SUCCESS_2,
    APACHE_BEAM_GIT_RECENT_SUCCESS_2,
    GOOGLE_API_CORE_RECENT_SUCCESS_2,
    GOOGLE_API_CORE_RECENT_SUCCESS_3,
    GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2,
    GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3,
    TENSORFLOW_RECENT_SUCCESS_3,
    TENSORFLOW_GIT_RECENT_SUCCESS_3,
    APACHE_BEAM_GOOGLE_API_CORE_RECENT_SUCCESS_2,
    APACHE_BEAM_GIT_GOOGLE_API_CORE_RECENT_SUCCESS_2,
    APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2,
    APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_GIT_RECENT_SUCCESS_2,
    APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2,
    APACHE_BEAM_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2,
    GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2,
    GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3,
    GOOGLE_API_CORE_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2,
    GOOGLE_API_CORE_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3,
    GOOGLE_API_CORE_TENSORFLOW_RECENT_SUCCESS_3,
    GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_SUCCESS_3,
    GOOGLE_API_PYTHON_CLIENT_TENSORFLOW_RECENT_SUCCESS_3,
]

UP_TO_DATE_DEPS = {
    'google-auth': {
        'current_time': datetime.datetime.utcnow(),
        'installed_version': '1.6.3',
        'installed_version_time': datetime.datetime(
            2019, 2, 19, 21, 15, 56),
        'is_latest': True,
        'latest_version': '1.6.3',
        'latest_version_time': datetime.datetime(
            2019, 2, 19, 21, 15, 56)
    },
    'grpcio': {
        'current_time': datetime.datetime.utcnow(),
        'installed_version': '1.19.0',
        'installed_version_time': datetime.datetime(
            2019, 2, 27, 0, 0, 53),
        'is_latest': True,
        'latest_version': '1.19.0',
        'latest_version_time': datetime.datetime(
            2019, 2, 27, 0, 0, 53)
    },

    # TODO: Replace with 'requests' once dependencies are properly added to
    # the existing compatibility results
    'google-api-core': {
        'current_time': datetime.datetime.utcnow(),
        'installed_version': '1.9.0',
        'installed_version_time': datetime.datetime(
            2019, 4, 5, 18, 1, 48),
        'is_latest': True,
        'latest_version': '1.9.0',
        'latest_version_time': datetime.datetime(
            2019, 4, 5, 18, 1, 48)
    },
}


class BadgeTestCase(unittest.TestCase):
    """Base class for tests of badge images."""

    def setUp(self):
        self.fake_store = fake_compatibility_store.CompatibilityStore()
        self.dependency_highlighter_stub = dependency_highlighter.DependencyHighlighter(
            store=self.fake_store)
        self.deprecated_dep_finder_stub = deprecated_dep_finder_stub.DeprecatedDepFinderStub(
        )

        main.app.config['TESTING'] = True
        self.client = main.app.test_client()

        self._store_patch = unittest.mock.patch('utils.store', self.fake_store)
        self._highlighter_patch = unittest.mock.patch(
            'utils.highlighter', self.dependency_highlighter_stub)
        self._finder_patch = unittest.mock.patch(
            'utils.finder', self.deprecated_dep_finder_stub)
        self._pkg_list_patch = unittest.mock.patch(
            'compatibility_lib.configs.PKG_LIST', [
                'apache-beam[gcp]',
                'google-api-core',
                'google-api-python-client',
                'tensorflow',
            ])
        self._whitelist_urls_patch = unittest.mock.patch(
            'compatibility_lib.configs.WHITELIST_URLS', {
                'git+git://github.com/google/apache-beam.git':
                    'apache-beam[gcp]',
                'git+git://github.com/google/api-core.git': 'google-api-core',
                'git+git://github.com/google/api-python-client.git':
                    'google-api-python-client',
                'git+git://github.com/google/tensorflow.git': 'tensorflow',
            })
        self._store_patch.start()
        self.addCleanup(self._store_patch.stop)
        self._highlighter_patch.start()
        self.addCleanup(self._highlighter_patch.stop)
        self._finder_patch.start()
        self.addCleanup(self._finder_patch.stop)
        self._pkg_list_patch.start()
        self.addCleanup(self._pkg_list_patch.stop)
        self._whitelist_urls_patch.start()
        self.addCleanup(self._whitelist_urls_patch.stop)

    def get_image_json(self, package):
        """Return the calculated badge data for a package as a dict."""
        return self.client.get(
            '/one_badge_image', query_string={
                'package': package
            }).get_json()

    def get_target_json(self, package):
        """Return the calculated details page data for a package as a dict."""
        return self.client.get(
            '/one_badge_target', query_string={
                'package': package
            }).get_json()

    def assertLinkUrl(self, package, actual_url):
        """Assert that the link for the badge image is correct for a package."""
        parsed_url = urllib.parse.urlparse(actual_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        self.assertEqual([package], params['package'])

    def _assertImageResponse(
            self, package_name, expected_status, expected_left_text):
        """Assert that the badge image response is correct for a package."""
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'], expected_left_text)
        self.assertEqual(json_response['right_text'], expected_status.value)
        self.assertEqual(json_response['right_color'],
                         main.BADGE_STATUS_TO_COLOR.get(expected_status))
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def _assertImageResponsePyPI(self, package_name, expected_status):
        """Assert that the badge image response is correct for a PyPI package."""
        self._assertImageResponse(
            package_name, expected_status, 'compatibility check (PyPI)')

    def _assertImageResponseGithub(self, package_name, expected_status):
        """Assert that the badge image response is correct for a github package."""
        self._assertImageResponse(
            package_name, expected_status, 'compatibility check (master)')

    def assertBadgeStatusToColor(self, badge_status_to_color):
        """Assert that the given badge status to color mapping is correct."""
        for status, color in badge_status_to_color.items():
            badge_status = main.BadgeStatus(status)
            self.assertEqual(main.BADGE_STATUS_TO_COLOR[badge_status], color)


class TestSuccess(BadgeTestCase):
    """Tests for the cases where the badge image displays 'success.'"""

    def setUp(self):
        BadgeTestCase.setUp(self)
        self.success_data = RECENT_SUCCESS_DATA

        # All of the CompatibilityResults in pairs_without_common_versions and
        # github_pairs have erroneous statuses but should still yield a
        # 'success' status as they should be skipped.
        self.pairs_without_common_versions = [
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3,
            GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2,
        ]
        self.github_pairs = [
            compatibility_store.CompatibilityResult(
                [
                    package.Package('git+git://github.com/google/apache-beam.git'),
                    package.Package('google-api-core')
                ],
                python_major_version=2,
                status=compatibility_store.Status.INSTALL_ERROR,
                timestamp=datetime.datetime.utcnow()),
            compatibility_store.CompatibilityResult(
                [
                    package.Package('git+git://github.com/google/tensorflow.git'),
                    package.Package('google-api-core')
                ],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                timestamp=datetime.datetime.utcnow()),
        ]

    def assertImageResponsePyPI(self, package_name):
        """Assert that the badge image response is correct for a PyPI package."""
        BadgeTestCase._assertImageResponsePyPI(
            self, package_name, main.BadgeStatus.SUCCESS)

    def assertImageResponseGithub(self, package_name):
        """Assert that the badge image response is correct for a github package."""
        BadgeTestCase._assertImageResponseGithub(
            self, package_name, main.BadgeStatus.SUCCESS)

    def assertTargetResponse(self, package_name, *supported_pyversions):
        expected_status = main.BadgeStatus.SUCCESS
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        # self compatibility result check
        for pyversion in ['py2', 'py3']:
            expected_details = utils.EMPTY_DETAILS
            if pyversion not in supported_pyversions:
                expected_details = ('The package does not support this '
                                    'version of python.')
            self.assertEqual(
                json_response['self_compat_res'][pyversion],
                {'details': expected_details, 'status': expected_status})

        # pair compatibility result check
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(expected_status, details={}))

        # dependency result check
        self.assertEqual(
            json_response['dependency_res'],
            {'deprecated_deps': '', 'details': {}, 'status': expected_status})

    def test_pypi_py2py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(self.success_data)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py2', 'py3')

    def test_git_py2py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(self.success_data)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py2', 'py3')

    def test_pypi_py2_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(self.success_data)
        package_name = 'apache-beam[gcp]'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py2')

    def test_git_py2_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(self.success_data)
        package_name = 'git+git://github.com/google/apache-beam.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py2')

    def test_pypi_py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(self.success_data)
        package_name = 'tensorflow'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py3')

    def test_git_py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(self.success_data)
        package_name = 'git+git://github.com/google/tensorflow.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py3')

    def test_pypi_py2py3_fresh_nodeps_ignore_pairs_without_common_versions(
            self):
        """Tests that pairs not sharing a common version are ignored."""
        fake_results = self.success_data + self.pairs_without_common_versions
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py2', 'py3')

    def test_git_py2py3_fresh_nodeps_ignore_pairs_without_common_versions(
            self):
        """Tests that pairs not sharing a common version are ignored."""
        fake_results = self.success_data + self.pairs_without_common_versions
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py2', 'py3')

    def test_pypi_py2py3_fresh_nodeps_ignore_git(self):
        """Tests that pair results containing git packages are ignored."""
        fake_results = self.success_data + self.github_pairs
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py2', 'py3')

    def test_git_py2py3_fresh_nodeps_ignore_git(self):
        """Tests that pair results containing git packages are ignored."""
        fake_results = self.success_data + self.github_pairs
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py2', 'py3')


class TestUnknownPackage(BadgeTestCase):
    """Tests for the cases where the badge image displays 'unknown package.'"""

    def assertImageResponsePyPI(self, package_name):
        """Assert that the badge image response is correct for a PyPI package."""
        BadgeTestCase._assertImageResponsePyPI(
            self, package_name, main.BadgeStatus.UNKNOWN_PACKAGE)

    def assertImageResponseGithub(self, package_name):
        """Assert that the badge image response is correct for a github package."""
        BadgeTestCase._assertImageResponseGithub(
            self, package_name, main.BadgeStatus.UNKNOWN_PACKAGE)

    def assertTargetResponse(self, package_name):
        expected_status = main.BadgeStatus.UNKNOWN_PACKAGE
        expected_details = ('This package is not a whitelisted google '
                            'python package; to whitelist a package, '
                            'contact the python team.')
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        # self compatibility result check
        self.assertEqual(
            json_response['self_compat_res'],
            utils._build_default_result(expected_status,
                                        details=expected_details))

        # pair compatibility result check
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(expected_status, details={}))

        # dependency result check
        self.assertEqual(
            json_response['dependency_res'],
            utils._build_default_result(expected_status, False, {}))

    def test_pypi_unknown_package(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'xxx'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name)

    def test_github_unknown_package(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'https://github.com/brianquinlan/notebooks'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name)


class TestMissingData(BadgeTestCase):
    """Tests for the cases where the badge image displays 'missing data.'"""

    def assertImageResponsePyPI(self, package_name):
        """Assert that the badge image response is correct for a PyPI package."""
        BadgeTestCase._assertImageResponsePyPI(
            self, package_name, main.BadgeStatus.MISSING_DATA)

    def test_missing_self_compatibility_data(self):
        package_name = 'google-api-core'
        missing_self_data = list(RECENT_SUCCESS_DATA)
        missing_self_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        self.fake_store.save_compatibility_statuses(missing_self_data)

        # Test badge image
        self.assertImageResponsePyPI(package_name)

        # Test badge details page
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        expected_status = main.BadgeStatus.MISSING_DATA
        expected_details = ("Missing data for packages=['google-api-core'], "
                            "versions=[2]")
        self.assertEqual(
            json_response['self_compat_res'],
            utils._build_default_result(expected_status,
                                        details=expected_details))

        expected_status = main.BadgeStatus.SUCCESS
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(expected_status, details={}))

        self.assertEqual(
            json_response['dependency_res'],
            {'deprecated_deps': '', 'details': {}, 'status': expected_status})

    def test_missing_pair_compatibility_data(self):
        package_name = 'google-api-core'
        missing_self_data = list(RECENT_SUCCESS_DATA)
        missing_self_data.remove(
            GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2)
        self.fake_store.save_compatibility_statuses(missing_self_data)

        # Test badge image
        self.assertImageResponsePyPI(package_name)

        # Test badge details page
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        expected_status = main.BadgeStatus.MISSING_DATA
        expected_details = {
            'google-api-python-client': (
                "Missing data for packages=['google-api-core', "
                "'google-api-python-client'], versions=[2]")
        }
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(expected_status,
                                        details=expected_details))

        expected_status = main.BadgeStatus.SUCCESS
        self.assertEqual(
            json_response['self_compat_res'],
            utils._build_default_result(expected_status))

        self.assertEqual(
            json_response['dependency_res'],
            {'deprecated_deps': '', 'details': {}, 'status': expected_status})


class TestSelfIncompatible(BadgeTestCase):
    """Tests for the cases where the badge image displays 'self incompatible.'"""

    def assertImageResponsePyPI(self, package_name):
        """Assert that the badge image response is correct for a PyPI package."""
        BadgeTestCase._assertImageResponsePyPI(
            self, package_name, main.BadgeStatus.SELF_INCOMPATIBLE)

    def assertImageResponseGithub(self, package_name):
        """Assert that the badge image response is correct for a github package."""
        BadgeTestCase._assertImageResponseGithub(
            self, package_name, main.BadgeStatus.SELF_INCOMPATIBLE)

    def assertTargetResponse(self, package_name, *affected_pyversions):
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        # self compatibility result check
        for pyversion in ['py2', 'py3']:
            expected_status = main.BadgeStatus.SELF_INCOMPATIBLE
            if pyversion not in affected_pyversions:
                expected_status = main.BadgeStatus.SUCCESS

            self.assertEqual(
                json_response['self_compat_res'][pyversion],
                {'details': utils.EMPTY_DETAILS, 'status': expected_status})

        # pair compatibility result check
        expected_status = main.BadgeStatus.SUCCESS
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(expected_status, details={}))

        # dependency result check
        self.assertEqual(
            json_response['dependency_res'],
            {'deprecated_deps': '', 'details': {}, 'status': expected_status})

    def test_pypi_py2py3_py2_incompatible_fresh_nodeps(self):
        package_name = 'google-api-core'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        self_incompatible_data.append(GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_2)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py2')

    def test_pypi_py2py3_py2_installation_failure_fresh_nodeps(self):
        package_name = 'google-api-core'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        self_incompatible_data.append(GOOGLE_API_CORE_RECENT_INSTALL_FAILURE_2)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py2')

    def test_github_py2py3_py2_incompatible_fresh_nodeps(self):
        package_name = 'git+git://github.com/google/api-core.git'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        self_incompatible_data.append(GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_2)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py2')

    def test_pypi_py2py3_py3_incompatible_fresh_nodeps(self):
        package_name = 'google-api-core'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        self_incompatible_data.append(GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_3)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(package_name, 'py3')

    def test_github_py2py3_py3_incompatible_fresh_nodeps(self):
        package_name = 'git+git://github.com/google/api-core.git'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        self_incompatible_data.append(GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_3)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(package_name, 'py3')


class TestBadgeImageDependency(TestSuccess):
    """Tests for cases with multiple dependencies displaying 'success'."""

    def setUp(self):
        TestSuccess.setUp(self)

        # Dependency Info
        dep_info = dict(UP_TO_DATE_DEPS)

        # Success Data: add up-to-date dependency information for all
        # CompatibilityResults containing a single package.
        self.success_data = []
        for compat_result in RECENT_SUCCESS_DATA:
            if len(compat_result.packages) == 1:
                compat_result = compat_result.with_updated_dependency_info(
                    dep_info)
            self.success_data.append(compat_result)


class TestOutdatedDependency(BadgeTestCase):
    """Tests for cases where the badge image displays 'old dependency.'"""

    def setUp(self):
        BadgeTestCase.setUp(self)

        self.off_by_minor_expected_details = {
            'google-auth': {
                'detail': 'google-auth is not up to date with the latest version',
                'installed_version': '1.4.0',
                'latest_version': '1.6.3',
                'priority': 'LOW_PRIORITY'
            }
        }

        self.off_by_patch_expected_details = {
            'google-auth': {
                'detail': 'google-auth is not up to date with the latest version',
                'installed_version': '1.6.0',
                'latest_version': '1.6.3',
                'priority': 'LOW_PRIORITY'
            }
        }

    def assertImageResponsePyPI(self, package_name):
        """Assert that the badge image response is correct for a PyPI package."""
        BadgeTestCase._assertImageResponsePyPI(
            self, package_name, main.BadgeStatus.OUTDATED_DEPENDENCY)

    def assertImageResponseGithub(self, package_name):
        """Assert that the badge image response is correct for a github package."""
        BadgeTestCase._assertImageResponseGithub(
            self, package_name, main.BadgeStatus.OUTDATED_DEPENDENCY)

    def assertTargetResponse(self, package_name, expected_details):
        expected_status = main.BadgeStatus.OUTDATED_DEPENDENCY
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        # self compatibility result check
        self.assertEqual(
            json_response['self_compat_res'],
            utils._build_default_result(main.BadgeStatus.SUCCESS,
                                        details=utils.EMPTY_DETAILS))

        # pair compatibility result check
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(main.BadgeStatus.SUCCESS, details={}))

        # dependency result check
        self.assertEqual(
            json_response['dependency_res'],
            {'deprecated_deps': '', 'details': expected_details, 'status': expected_status})

    def test_pypi_py2py3_off_by_minor(self):
        old_dep_info = dict(UP_TO_DATE_DEPS)
        old_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '1.4.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        old_dep_compat_results = list(RECENT_SUCCESS_DATA)
        old_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        old_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        old_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_2.with_updated_dependency_info(
                old_dep_info))
        old_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_3.with_updated_dependency_info(
                old_dep_info))

        self.fake_store.save_compatibility_statuses(old_dep_compat_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_minor_expected_details)

    def test_git_py2py3_off_by_minor(self):
        old_dep_info = dict(UP_TO_DATE_DEPS)
        old_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '1.4.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        old_dep_compat_results = list(RECENT_SUCCESS_DATA)
        old_dep_compat_results.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        old_dep_compat_results.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        old_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2.with_updated_dependency_info(
                old_dep_info))
        old_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3.with_updated_dependency_info(
                old_dep_info))

        self.fake_store.save_compatibility_statuses(old_dep_compat_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_minor_expected_details)

    def test_pypi_py2py3_off_by_patch(self):
        old_dep_info = dict(UP_TO_DATE_DEPS)
        old_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '1.6.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        old_dep_compat_results = list(RECENT_SUCCESS_DATA)
        old_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        old_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        old_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_2.with_updated_dependency_info(
                old_dep_info))
        old_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_3.with_updated_dependency_info(
                old_dep_info))

        self.fake_store.save_compatibility_statuses(old_dep_compat_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_patch_expected_details)

    def test_git_py2py3_off_by_patch(self):
        old_dep_info = dict(UP_TO_DATE_DEPS)
        old_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '1.6.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        old_dep_compat_results = list(RECENT_SUCCESS_DATA)
        old_dep_compat_results.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        old_dep_compat_results.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        old_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2.with_updated_dependency_info(
                old_dep_info))
        old_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3.with_updated_dependency_info(
                old_dep_info))

        self.fake_store.save_compatibility_statuses(old_dep_compat_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_patch_expected_details)


class TestObsoleteDependency(BadgeTestCase):
    """Tests for cases where the badge image displays 'obsolete dependency'."""

    def setUp(self):
        BadgeTestCase.setUp(self)

        self.off_by_major_expected_details = {
            'google-auth': {
                'detail': ('google-auth is 1 or more major versions behind '
                           'the latest version'),
                'installed_version': '0.9.9',
                'latest_version': '1.6.3',
                'priority': 'HIGH_PRIORITY'
            }
        }

        self.off_by_minor_expected_details = {
            'google-auth': {
                'detail': ('google-auth is 3 or more minor versions behind '
                           'the latest version'),
                'installed_version': '1.3.0',
                'latest_version': '1.6.3',
                'priority': 'HIGH_PRIORITY'
            }
        }

        self.expired_major_grace_period_expected_details = {
            'google-auth': {
                'detail': ('it has been over 30 days since the major version '
                           'for google-auth was released'),
                'installed_version': '0.9.9',
                'latest_version': '1.0.0',
                'priority': 'HIGH_PRIORITY'
            }
        }

        self.expired_default_grace_period_expected_details = {
            'google-auth': {
                'detail': ('it has been over 6 months since the latest '
                           'version for google-auth was released'),
                'installed_version': '1.3.0',
                'latest_version': '1.0.0',
                'priority': 'HIGH_PRIORITY'
            }
        }

    def assertImageResponsePyPI(self, package_name):
        """Assert that the badge image response is correct for a PyPI package."""
        BadgeTestCase._assertImageResponsePyPI(
            self, package_name, main.BadgeStatus.OBSOLETE_DEPENDENCY)

    def assertImageResponseGithub(self, package_name):
        """Assert that the badge image response is correct for a github package."""
        BadgeTestCase._assertImageResponseGithub(
            self, package_name, main.BadgeStatus.OBSOLETE_DEPENDENCY)

    def assertTargetResponse(self, package_name, expected_details):
        expected_status = main.BadgeStatus.OBSOLETE_DEPENDENCY
        json_response = self.get_target_json(package_name)
        self.assertEqual(json_response['package_name'], package_name)
        self.assertBadgeStatusToColor(json_response['badge_status_to_color'])

        # self compatibility result check
        self.assertEqual(
            json_response['self_compat_res'],
            utils._build_default_result(main.BadgeStatus.SUCCESS,
                                        details=utils.EMPTY_DETAILS))

        # pair compatibility result check
        self.assertEqual(
            json_response['google_compat_res'],
            utils._build_default_result(main.BadgeStatus.SUCCESS, details={}))

        # dependency result check
        self.assertEqual(
            json_response['dependency_res'],
            {'deprecated_deps': '', 'details': expected_details, 'status': expected_status})

    def test_pypi_py2py3_off_by_major(self):
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '0.9.9',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_major_expected_details)

    def test_git_py2py3_off_by_major(self):
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '0.9.9',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_major_expected_details)

    def test_pypi_py2py3_off_by_minor(self):
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '1.3.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_minor_expected_details)

    def test_git_py2py3_off_by_minor(self):
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime.utcnow(),
            'installed_version': '1.3.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.6.3',
            'latest_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(
            package_name, self.off_by_minor_expected_details)

    def test_pypi_py2py3_expired_major_grace_period(self):
        """Tests that "old dependency" eventually changes to "obsolete ..."."""
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime(2019, 3, 23, 0, 0, 0),
            'installed_version': '0.9.9',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.0.0',
            'latest_version_time': datetime.datetime(2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(
            package_name, self.expired_major_grace_period_expected_details)

    def test_git_py2py3_expired_major_grace_period(self):
        """Tests that "old dependency" eventually changes to "obsolete ..."."""
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime(2019, 3, 23, 0, 0, 0),
            'installed_version': '0.9.9',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.0.0',
            'latest_version_time': datetime.datetime(2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(
            package_name, self.expired_major_grace_period_expected_details)

    def test_pypi_py2py3_expired_default_grace_period(self):
        """Tests that "old dependency" eventually changes to "obsolete ..."."""
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime(2019, 8, 23, 0, 0, 0),
            'installed_version': '1.3.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.0.0',
            'latest_version_time': datetime.datetime(2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'google-api-core'
        self.assertImageResponsePyPI(package_name)
        self.assertTargetResponse(
            package_name, self.expired_default_grace_period_expected_details)

    def test_git_py2py3_expired_default_grace_period(self):
        """Tests that "old dependency" eventually changes to "obsolete ..."."""
        obsolete_dep_info = dict(UP_TO_DATE_DEPS)
        obsolete_dep_info['google-auth'] = {
            'current_time': datetime.datetime(2019, 8, 23, 0, 0, 0),
            'installed_version': '1.3.0',
            'installed_version_time': datetime.datetime(
                2019, 2, 19, 21, 15, 56),
            'is_latest': False,
            'latest_version': '1.0.0',
            'latest_version_time': datetime.datetime(2019, 2, 19, 21, 15, 56)
        }

        obsolete_dep_compat_results = list(RECENT_SUCCESS_DATA)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        obsolete_dep_compat_results.remove(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2.with_updated_dependency_info(
                obsolete_dep_info))
        obsolete_dep_compat_results.append(
            GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3.with_updated_dependency_info(
                obsolete_dep_info))

        self.fake_store.save_compatibility_statuses(
            obsolete_dep_compat_results)
        package_name = 'git+git://github.com/google/api-core.git'
        self.assertImageResponseGithub(package_name)
        self.assertTargetResponse(
            package_name, self.expired_default_grace_period_expected_details)
