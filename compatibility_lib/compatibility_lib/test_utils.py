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
import unittest


class Test__parse_datetime(unittest.TestCase):

  def test__parse_datetime(self):
    from compatibility_lib import utils

    date_string = '2018-08-16T15:42:04.351677'
    expected = '2018-08-16 00:00:00'
    res = utils._parse_datetime(date_string)
    self.assertEqual(str(res), expected)
