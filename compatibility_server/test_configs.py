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

"""Tests for configs."""

import os
import unittest


class TestConfigs(unittest.TestCase):

    @unittest.skip('TODO: unskip after letting new data populate')
    def test_config_files_match(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        root, _ = os.path.split(cwd)
        first_path = os.path.join(cwd, 'configs.py')
        second_path = os.path.join(
            root, 'compatibility_lib/compatibility_lib/configs.py')
        with open(first_path) as fd:
            first_file = fd.read()
        with open(second_path) as fd:
            second_file = fd.read()
        self.assertEqual(first_file, second_file)
