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

import mock
import os
import unittest


os.environ["RUN_LOCALLY"] = 'true'

# Set the cache to use local cache before importing the main module
import main


class TestBadgeServer(unittest.TestCase):

    def test__get_badge_use_py2(self):
        package_name = 'package-1'
        res = {
            'py2': {
                'status': 'CHECK_WARNING', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }

        image = main.badge_utils._get_badge(res, package_name)

        self.assertIn(package_name, image)
        self.assertIn("CHECK WARNING", image)

    def test__get_badge_use_py3(self):
        package_name = 'package-1'
        res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'CHECK_WARNING', 'details': {}
            }
        }

        image = main.badge_utils._get_badge(res, package_name)

        self.assertIn(package_name, image)
        self.assertIn("CHECK WARNING", image)

    def test__get_all_results_from_cache_success(self):
        self_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }

        google_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }

        dep_res = {
            'status': 'UP_TO_DATE',
            'details': {},
        }

        main.cache.set("opencensus_self_comp_badge", self_res)
        main.cache.set("opencensus_google_comp_badge", google_res)
        main.cache.set("opencensus_dependency_badge", dep_res)

        status, _, _, _, _ = main._get_all_results_from_cache(
            'opencensus')

        self.assertEqual(status, 'SUCCESS')

    def test__get_all_results_from_cache_calculating(self):
        self_res = {
            'py2': {
                'status': 'CALCULATING', 'details': {}
            },
            'py3': {
                'status': 'CALCULATING', 'details': {}
            }
        }

        google_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }

        dep_res = {
            'status': 'UP_TO_DATE',
            'details': {},
        }

        main.cache.set("opencensus_self_comp_badge", self_res)
        main.cache.set("opencensus_google_comp_badge", google_res)
        main.cache.set("opencensus_dependency_badge", dep_res)

        status, _, _, _, _ = main._get_all_results_from_cache(
            'opencensus')

        self.assertEqual(status, 'CALCULATING')

    def test__get_all_results_from_cache_check_warning(self):
        self_res = {
            'py2': {
                'status': 'CHECK_WARNING', 'details': {}
            },
            'py3': {
                'status': 'CHECK_WARNING', 'details': {}
            }
        }

        google_res = {
            'py2': {
                'status': 'SUCCESS', 'details': {}
            },
            'py3': {
                'status': 'SUCCESS', 'details': {}
            }
        }

        dep_res = {
            'status': 'UP_TO_DATE',
            'details': {},
        }

        main.cache.set("opencensus_self_comp_badge", self_res)
        main.cache.set("opencensus_google_comp_badge", google_res)
        main.cache.set("opencensus_dependency_badge", dep_res)

        status, _, _, _, _ = main._get_all_results_from_cache(
            'opencensus')

        self.assertEqual(status, 'CHECK_WARNING')
