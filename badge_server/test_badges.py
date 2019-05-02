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
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/apache-beam.git')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.CHECK_WARNING,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=3,
    status=compatibility_store.Status.CHECK_WARNING,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=2,
    status=compatibility_store.Status.CHECK_WARNING,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=3,
    status=compatibility_store.Status.CHECK_WARNING,
    timestamp=datetime.datetime.utcnow())

TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('tensorflow')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

TENSORFLOW_GIT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/tensorflow.git')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('apache-beam[gcp]'),
     package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3 = compatibility_store.CompatibilityResult(
    [package.Package('apache-beam[gcp]'),
     package.Package('google-api-core')],
    python_major_version=3,   # apache-beam does not support Python 3
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GIT_GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/apache-beam.git'),
     package.Package('google-api-core')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/apache-beam.git'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('git+git://github.com/google/api-core.git')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('git+git://github.com/google/api-core.git')
    ],
    python_major_version=3,   # apache-beam does not support Python 3
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('apache-beam[gcp]'),
        package.Package('git+git://github.com/google/api-python-client.git')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-core'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-core'),
        package.Package('google-api-python-client')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('google-api-python-client')
    ],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('google-api-python-client')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core'),
     package.Package('tensorflow')],
    python_major_version=2,   # tensorflow does not support Python 2
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core'),
     package.Package('tensorflow')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('tensorflow')
    ],
    python_major_version=2,   # tensorflow does not support Python 2
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('git+git://github.com/google/api-core.git'),
        package.Package('tensorflow')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_PYTHON_CLIENT_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-python-client'),
        package.Package('tensorflow')
    ],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

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


class BadgeImageTestCase(unittest.TestCase):
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

    def assertLinkUrl(self, package, actual_url):
        """Assert that the link for the badge image is correct for a package."""
        parsed_url = urllib.parse.urlparse(actual_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        self.assertEqual([package], params['package'])


class TestBadgeImageSuccess(BadgeImageTestCase):
    """Tests for the cases where the badge image displays 'success.'"""

    def test_pypi_py2py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'google-api-core'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_git_py2py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'git+git://github.com/google/api-core.git'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_pypi_py2_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'apache-beam[gcp]'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_git_py2_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'git+git://github.com/google/apache-beam.git'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_pypi_py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'tensorflow'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_git_py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'git+git://github.com/google/tensorflow.git'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_pypi_py2py3_fresh_nodeps_ignore_unsupported_versions(self):
        """Tests that pairs not sharing a common version are ignored."""
        fake_results = RECENT_SUCCESS_DATA + [
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3,
            GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2,
        ]
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'google-api-core'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_git_py2py3_fresh_nodeps_ignore_unsupported_versions(self):
        """Tests that pairs not sharing a common version are ignored."""
        fake_results = RECENT_SUCCESS_DATA + [
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3,
            GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2,
        ]
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'git+git://github.com/google/api-core.git'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_pypi_py2py3_fresh_nodeps_ignore_git(self):
        """Tests that pair results containing git packages are ignored."""
        fake_results = RECENT_SUCCESS_DATA + [
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
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'google-api-core'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_git_py2py3_fresh_nodeps_ignore_git(self):
        """Tests that pair results containing git packages are ignored."""
        fake_results = RECENT_SUCCESS_DATA + [
            compatibility_store.CompatibilityResult(
                [
                    package.Package('git+git://github.com/google/apache-beam.git'),
                    package.Package('git+git://github.com/google/api-core.git')
                ],
                python_major_version=2,
                status=compatibility_store.Status.INSTALL_ERROR,
                timestamp=datetime.datetime.utcnow()),
            compatibility_store.CompatibilityResult(
                [
                    package.Package('git+git://github.com/google/tensorflow.git'),
                    package.Package('git+git://github.com/google/api-core.git')
                ],
                python_major_version=3,
                status=compatibility_store.Status.INSTALL_ERROR,
                timestamp=datetime.datetime.utcnow()),
        ]
        self.fake_store.save_compatibility_statuses(fake_results)
        package_name = 'git+git://github.com/google/api-core.git'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package_name, json_response['whole_link'])


class TestBadgeImageUnknownPackage(BadgeImageTestCase):
    """Tests for the cases where the badge image displays 'unknown package.'"""

    def test_pypi_unknown_package(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'xxx'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'unknown package')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_github_unknown_package(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package_name = 'https://github.com/brianquinlan/notebooks'
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'unknown package')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package_name, json_response['whole_link'])


class TestBadgeImageMissingData(BadgeImageTestCase):
    """Tests for the cases where the badge image displays 'missing data.'"""

    def test_missing_self_compatibility_data(self):
        package_name = 'google-api-core'
        missing_self_data = list(RECENT_SUCCESS_DATA)
        missing_self_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        self.fake_store.save_compatibility_statuses(missing_self_data)

        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'missing data')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_missing_pair_compatibility_data(self):
        package_name = 'google-api-core'
        missing_self_data = list(RECENT_SUCCESS_DATA)
        missing_self_data.remove(
            GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2)
        self.fake_store.save_compatibility_statuses(missing_self_data)

        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'missing data')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package_name, json_response['whole_link'])


class TestSelfIncompatible(BadgeImageTestCase):
    """Tests for the cases where the badge image displays 'self incompatible.'"""

    def test_pypi_py2py3_py2_incompatible_fresh_nodeps(self):
        package_name = 'google-api-core'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        self_incompatible_data.append(GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_2)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)

        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'self incompatible')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_github_py2py3_py2_incompatible_fresh_nodeps(self):
        package_name = 'git+git://github.com/google/api-core.git'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2)
        self_incompatible_data.append(GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_2)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)

        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'self incompatible')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_pypi_py2py3_py3_incompatible_fresh_nodeps(self):
        package_name = 'google-api-core'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_3)
        self_incompatible_data.append(GOOGLE_API_CORE_RECENT_SELF_INCOMPATIBLE_3)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)

        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'self incompatible')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

    def test_github_py2py3_py3_incompatible_fresh_nodeps(self):
        package_name = 'git+git://github.com/google/api-core.git'
        self_incompatible_data = list(RECENT_SUCCESS_DATA)
        self_incompatible_data.remove(GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3)
        self_incompatible_data.append(GOOGLE_API_CORE_GIT_RECENT_SELF_INCOMPATIBLE_3)
        self.fake_store.save_compatibility_statuses(self_incompatible_data)

        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'self incompatible')


class TestBadgeImageOutdatedDependency(BadgeImageTestCase):
    """Tests for cases where the badge image displays 'old dependency.'"""

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'old dependency')
        self.assertEqual(json_response['right_color'], '#A4A61D')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'old dependency')
        self.assertEqual(json_response['right_color'], '#A4A61D')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'old dependency')
        self.assertEqual(json_response['right_color'], '#A4A61D')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'old dependency')
        self.assertEqual(json_response['right_color'], '#A4A61D')
        self.assertLinkUrl(package_name, json_response['whole_link'])


class TestBadgeImageObsoleteDependency(BadgeImageTestCase):
    """Tests for cases where the badge image displays 'obsolete dependency.'"""

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])

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
        json_response = self.get_image_json(package_name)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'obsolete dependency')
        self.assertEqual(json_response['right_color'], '#E05D44')
        self.assertLinkUrl(package_name, json_response['whole_link'])
