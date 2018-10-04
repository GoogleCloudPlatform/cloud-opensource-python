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

from compatibility_lib.package_crawler_static import get_package_info, get_module_info


class TestSimplePackages(unittest.TestCase):
    def setUp(self):
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.cwd = os.path.join(self.cwd, 'testpkgs')

    def test_simple_function(self):
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
        location = os.path.join(self.cwd, 'simple_function')
        info = get_package_info(location)
        self.assertEqual(expected, info)

