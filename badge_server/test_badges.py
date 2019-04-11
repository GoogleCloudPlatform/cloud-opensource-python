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
from compatibility_lib import dependency_highlighter_stub
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

GOOGLE_API_CORE_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_GIT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/api-core.git')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
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

APACHE_BEAM_GIT_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3 = compatibility_store.CompatibilityResult(
    [package.Package('git+git://github.com/google/apache-beam.git'),
     package.Package('google-api-core')],
    python_major_version=3,   # apache-beam does not support Python 3
    status=compatibility_store.Status.INSTALL_ERROR,
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

GOOGLE_API_CORE_TENSORFLOW_GIT_RECENT_INSTALL_ERROR_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-core'),
        package.Package('git+git://github.com/google/tensorflow.git'),
    ],
    python_major_version=2,   # tensorflow does not support Python 2
    status=compatibility_store.Status.INSTALL_ERROR,
    timestamp=datetime.datetime.utcnow())

GOOGLE_API_CORE_TENSORFLOW_GIT_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-core'),
        package.Package('git+git://github.com/google/tensorflow.git')
    ],
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


class BadgeImageTestCase(unittest.TestCase):
    """Base class for tests of badge images."""

    def setUp(self):
        self.fake_store = fake_compatibility_store.CompatibilityStore()
        self.dependency_highlighter_stub = dependency_highlighter_stub.DependencyHighlighterStub(
        )
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
        package = 'google-api-core'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_git_py2py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'git+git://github.com/google/api-core.git'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_pypi_py2_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'apache-beam[gcp]'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_git_py2_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'git+git://github.com/google/apache-beam.git'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_pypi_py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'tensorflow'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_git_py3_fresh_nodeps(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'git+git://github.com/google/tensorflow.git'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_pypi_mix_fresh_nodeps(self):
        RECENT_SUCCESS_DATA_EXTRA = RECENT_SUCCESS_DATA + [
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GIT_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_TENSORFLOW_GIT_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_TENSORFLOW_GIT_RECENT_SUCCESS_3,
            GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2,
        ]
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA_EXTRA)
        package = 'google-api-core'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_git_mix_fresh_nodeps(self):
        RECENT_SUCCESS_DATA_EXTRA = RECENT_SUCCESS_DATA + [
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GOOGLE_API_CORE_GIT_RECENT_INSTALL_ERROR_3,
            APACHE_BEAM_GIT_GOOGLE_API_CORE_RECENT_INSTALL_ERROR_3,
            GOOGLE_API_CORE_TENSORFLOW_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_TENSORFLOW_GIT_RECENT_INSTALL_ERROR_2,
            GOOGLE_API_CORE_TENSORFLOW_GIT_RECENT_SUCCESS_3,
            GOOGLE_API_CORE_GIT_TENSORFLOW_RECENT_INSTALL_ERROR_2,
        ]
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA_EXTRA)
        package = 'git+git://github.com/google/api-core.git'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], '#44CC44')
        self.assertLinkUrl(package, json_response['whole_link'])


class TestBadgeImageUnknownPackage(BadgeImageTestCase):
    """Tests for the cases where the badge image displays 'unknown package.'"""

    def test_pypi_unknown_package(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'xxx'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'unknown package')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_github_unknown_package(self):
        self.fake_store.save_compatibility_statuses(RECENT_SUCCESS_DATA)
        package = 'https://github.com/brianquinlan/notebooks'
        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'unknown package')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package, json_response['whole_link'])


class TestBadgeImageMissingData(BadgeImageTestCase):
    """Tests for the cases where the badge image displays 'missing data.'"""

    def test_missing_self_compatibility_data(self):
        package = 'google-api-core'
        missing_self_data = list(RECENT_SUCCESS_DATA)
        missing_self_data.remove(GOOGLE_API_CORE_RECENT_SUCCESS_2)
        self.fake_store.save_compatibility_statuses(missing_self_data)

        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'missing data')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package, json_response['whole_link'])

    def test_missing_pair_compatibility_data(self):
        package = 'google-api-core'
        missing_self_data = list(RECENT_SUCCESS_DATA)
        missing_self_data.remove(
            GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2)
        self.fake_store.save_compatibility_statuses(missing_self_data)

        json_response = self.get_image_json(package)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'missing data')
        self.assertEqual(json_response['right_color'], '#9F9F9F')
        self.assertLinkUrl(package, json_response['whole_link'])
