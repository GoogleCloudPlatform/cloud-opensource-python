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
import json
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

TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('tensorflow')],
    python_major_version=3,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_CORE_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core'),
     package.Package('apache-beam[gcp]')],
    python_major_version=2,
    status=compatibility_store.Status.SUCCESS,
    timestamp=datetime.datetime.utcnow())

APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2 = compatibility_store.CompatibilityResult(
    [
        package.Package('google-api-python-client'),
        package.Package('apache-beam[gcp]')
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

GOOGLE_API_CORE_TENSORFLOW_RECENT_SUCCESS_3 = compatibility_store.CompatibilityResult(
    [package.Package('google-api-core'),
     package.Package('tensorflow')],
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


class TestBadgeServer(unittest.TestCase):
    def setUp(self):
        self.fake_store = fake_compatibility_store.CompatibilityStore()
        self.dependency_highlighter_stub = dependency_highlighter_stub.DependencyHighlighterStub(
        )
        self.deprecated_dep_finder_stub = deprecated_dep_finder_stub.DeprecatedDepFinderStub(
        )
        self.client = main.app.test_client()

        utils.store = self.fake_store
        utils.highlighter = self.dependency_highlighter_stub
        utils.finder = self.deprecated_dep_finder_stub
        main.configs.PKG_LIST = [
            'apache-beam[gcp]',
            'google-api-core',
            'google-api-python-client',
            'tensorflow',
        ]

    def _get_image(self, package):
        return self.client.get(
            '/one_badge_image', query_string={'package': package})

    def _get_image_json(self, package):
        response = self._get_image(package)
        return json.loads(response.data)

    @unittest.skip
    def test_pypi_success(self):
        self.fake_store.save_compatibility_statuses([
            GOOGLE_API_CORE_RECENT_SUCCESS_2,
            GOOGLE_API_CORE_RECENT_SUCCESS_3,
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_SUCCESS_2,
            GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2,
            GOOGLE_API_CORE_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_3,
            GOOGLE_API_PYTHON_CLIENT_TENSORFLOW_RECENT_SUCCESS_3,
        ])
        json_response = self._get_image_json('google-api-core')
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], 'brightgreen')
        self.assertIn('package=google-api-core', json_response['whole_link'])

    @unittest.skip
    def test_pypi_success_py_3_only(self):
        self.fake_store.save_compatibility_statuses([
            TENSORFLOW_RECENT_SUCCESS_3,
            GOOGLE_API_CORE_TENSORFLOW_RECENT_SUCCESS_3,
            GOOGLE_API_PYTHON_CLIENT_TENSORFLOW_RECENT_SUCCESS_3
        ])
        json_response = self._get_image_json('tensorflow')
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], 'brightgreen')
        self.assertIn('package=tensorflow', json_response['whole_link'])

    @unittest.skip
    def test_pypi_success_py_2_only(self):
        self.fake_store.save_compatibility_statuses([
            APACHE_BEAM_RECENT_SUCCESS_2,
            APACHE_BEAM_GOOGLE_API_CORE_RECENT_SUCCESS_2,
            APACHE_BEAM_GOOGLE_API_PYTHON_CLIENT_RECENT_SUCCESS_2
        ])
        json_response = self._get_image_json('apache-beam[gcp]')
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'success')
        self.assertEqual(json_response['right_color'], 'brightgreen')
        self.assertIn('package=apache[beam]', json_response['whole_link'])

    def test_pypi_unknown_package(self):
        json_response = self._get_image_json('xxx')
        self.assertEqual(json_response['left_text'],
                         'compatibility check (PyPI)')
        self.assertEqual(json_response['right_text'], 'unknown package')
        self.assertEqual(json_response['right_color'], 'lightgrey')
        self.assertIn('package=xxx', json_response['whole_link'])

    def test_github_unknown_package(self):
        url = 'https://github.com/brianquinlan/notebooks'
        encoded_url = urllib.parse.quote_plus(url)
        json_response = self._get_image_json(url)
        self.assertEqual(json_response['left_text'],
                         'compatibility check (master)')
        self.assertEqual(json_response['right_text'], 'unknown package')
        self.assertEqual(json_response['right_color'], 'lightgrey')
        self.assertIn('package={}'.format(encoded_url),
                      json_response['whole_link'])
