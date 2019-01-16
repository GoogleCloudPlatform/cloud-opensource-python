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

"""Perform a load test on the compatibility server. Usage:

$ pip install locustio
$ locust --host=http://104.197.8.72
"""

import random
import urllib.parse

import locust


PYTHON2_PACKAGES = [
    'apache-beam[gcp]',
    'google-cloud-bigtable',
    'google-cloud-dns',
    'google-cloud-vision',
    'tensorboard',
    'tensorflow',
]

PYTHON3_PACKAGES = [
    'google-cloud-bigtable',
    'google-cloud-dns',
    'google-cloud-vision',
    'tensorboard',
    'tensorflow',
]


class CompatibilityCheck(locust.TaskSet):
    @locust.task
    def single_python2(self):
        query = urllib.parse.urlencode(
            {'python-version': '2',
             'package': random.choice(PYTHON2_PACKAGES)})
        self.client.get('/?%s' % query)

    @locust.task
    def single_python3(self):
        query = urllib.parse.urlencode(
            {'python-version': '3',
             'package': random.choice(PYTHON3_PACKAGES)})
        self.client.get('/?%s' % query)

    @locust.task
    def double_python2(self):
        package1 = random.choice(PYTHON2_PACKAGES)
        package2 = random.choice(list(set(PYTHON2_PACKAGES) - {package1}))

        query = urllib.parse.urlencode([('python-version', '2'),
                                        ('package', package1),
                                        ('package', package2)])
        self.client.get('/?%s' % query)

    @locust.task
    def double_python3(self):
        package1 = random.choice(PYTHON3_PACKAGES)
        package2 = random.choice(list(set(PYTHON3_PACKAGES) - {package1}))

        query = urllib.parse.urlencode([('python-version', '3'),
                                        ('package', package1),
                                        ('package', package2)])
        self.client.get('/?%s' % query)


class CompatibilityChecker(locust.HttpLocust):
    task_set = CompatibilityCheck
    min_wait = 0
    max_wait = 0
