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
                            'args': {
                                'single_args': [],
                                'defaults': {},
                                'vararg': None,
                                'kwarg': None
                            }
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
        expected = ['main: missing arg "bar"']
        self.assertEqual(expected, res)

    def test_semver_check_on_added_args(self):
        old_dir = os.path.join(TEST_DIR, 'added_args/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'added_args/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['main.Foo: expected 2 required args, got 3',
                    'main.bar: expected 0 required args, got 1']
        self.assertEqual(expected, res)

    def test_semver_check_on_removed_args(self):
        old_dir = os.path.join(TEST_DIR, 'removed_args/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'removed_args/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['main.Foo: expected 2 args, got 1',
                    'main.bar: expected 1 args, got 0']
        self.assertEqual(expected, res)

    def test_semver_check_on_added_optional_args(self):
        ver1 = os.path.join(TEST_DIR, 'optional_args/appended/0.1.0')
        ver2 = os.path.join(TEST_DIR, 'optional_args/appended/0.2.0')
        ver3 = os.path.join(TEST_DIR, 'optional_args/appended/0.3.0')

        res12 = check(ver1, ver2)
        res23 = check(ver2, ver3)
        res13 = check(ver1, ver3)

        self.assertEqual([], res12)
        self.assertEqual([], res23)
        self.assertEqual([], res13)

    def test_semver_check_on_removed_optional_args(self):
        old_dir = os.path.join(TEST_DIR, 'optional_args/removed/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'optional_args/removed/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['main.Foo: expected 3 args, got 2',
                    'main.bar: missing arg "d"',
                    'main.baz: expected 1 args, got 0']
        self.assertEqual(expected, res)

    def test_semver_check_on_inserted_optional_args(self):
        old_dir = os.path.join(TEST_DIR, 'optional_args/inserted/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'optional_args/inserted/0.2.0')

        res = check(old_dir, new_dir)
        expected = ['main.Foo: bad arg name; expected "y", got "z"']
        self.assertEqual(expected, res)

    def test_semver_check_on_modified_optional_args(self):
        old_dir = os.path.join(TEST_DIR, 'optional_args/modified/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'optional_args/modified/0.2.0')

        res = check(old_dir, new_dir)
        expected = [('main.Foo: default value was not preserved; '
                     'expecting "y=None", got "y=True"'),
                    ('main.bar: default value was not preserved; '
                     'expecting "c=1", got "c=2"'),
                    ('main.bar: default value was not preserved; '
                     'expecting "d=2", got "d=1"'),
                    'main.baz: bad arg name; expected "name", got "first_name"']
        for errmsg in res:
            self.assertTrue(errmsg in expected)

    def test_semver_check_on_converted_optional_args(self):
        old_dir = os.path.join(TEST_DIR, 'optional_args/converted/0.1.0')
        new_dir = os.path.join(TEST_DIR, 'optional_args/converted/0.2.0')

        res = check(old_dir, new_dir)
        self.assertEqual([], res)
