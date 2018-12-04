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

import ast
import os
import unittest

from compatibility_lib.semver_checker import check
from compatibility_lib.package_crawler_static import get_package_info, get_module_info


CWD = os.path.dirname(os.path.realpath(__file__))
TEST_DIR = os.path.join(CWD, 'testpkgs')


class TestSimplePackages(unittest.TestCase):

    def test_get_package_info(self):
        expected = {
            'modules': {
                'simple_function': {
                    'classes': {},
                    'functions': {
                        'hello': {
                            'args': []
                        }
                    }
                },
            },
            'subpackages': {}
        }
        location = os.path.join(TEST_DIR, 'simple_function')
        info = get_package_info(location)
        self.assertEqual(expected, info)

    def test_semver_check_on_added_func(self):
        old_dir = os.path.join(TEST_DIR, 'added_func/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'added_func/0.2.0')

        res = check(old_dir, new_dir)
        self.assertEqual([], res)

    def test_semver_check_on_removed_func(self):
        old_dir = os.path.join(TEST_DIR, 'removed_func/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'removed_func/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['missing attribute "bar" from new version']
        self.assertEqual(expected, res)

    def test_semver_check_on_added_args(self):
        old_dir = os.path.join(TEST_DIR, 'added_args/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'added_args/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['args do not match; expecting: "self, x", got: "self, x, y"']
        self.assertEqual(expected, res)

    def test_semver_check_on_removed_args(self):
        old_dir = os.path.join(TEST_DIR, 'removed_args/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'removed_args/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['args do not match; expecting: "self, x", got: "self"']
        self.assertEqual(expected, res)
