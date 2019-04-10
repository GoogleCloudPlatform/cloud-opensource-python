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
"""Add tests for the badge server all badges page."""

import unittest
import unittest.mock

import main
import utils


class AllBadgesTestCase(unittest.TestCase):
  """Test case for the badge server all badges endpoint."""

  def setUp(self):
    main.app.config['TESTING'] = True
    self.client = main.app.test_client()

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

    self._pkg_list_patch.start()
    self.addCleanup(self._pkg_list_patch.stop)
    self._whitelist_urls_patch.start()
    self.addCleanup(self._whitelist_urls_patch.stop)

  def test_all(self):
    html = self.client.get('/all').get_data(as_text=True)

    self.assertIn('apache-beam[gcp]', html)
    self.assertIn('https://pypi.org/project/apache-beam', html)
    self.assertIn('https://github.com/google/apache-beam.git', html)
    self.assertIn(
        '/one_badge_target?package=apache-beam%5Bgcp%5D',
        html)
    self.assertIn(
        '/one_badge_image?package=apache-beam%5Bgcp%5D',
        html)
    self.assertIn(
        '/one_badge_target?package=git%2Bgit%3A//github.com/google/apache-beam.git',
        html)
    self.assertIn(
        '/one_badge_image?package=git%2Bgit%3A//github.com/google/apache-beam.git',
        html)
