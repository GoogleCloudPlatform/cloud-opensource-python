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
import requests
import signal
import subprocess
import time

from retrying import retry

import unittest

HOST_PORT = '0.0.0.0:8888'
BASE_URL = 'http://0.0.0.0:8888/'
PACKAGE_FOR_TEST = 'opencensus'

RETRY_WAIT_PERIOD = 8000 # Wait 8 seconds between each retry
RETRY_MAX_ATTEMPT = 10 # Retry 10 times


def wait_app_to_start():
    """Wait the application to start running."""
    url = '{}?package={}&python-version={}'.format(
        BASE_URL, PACKAGE_FOR_TEST, 3)
    cmd = 'wget --retry-connrefused --tries=5 \'{}\''.format(url)
    subprocess.check_call(cmd, shell=True)


def run_application():
    """Start running the compatibility checker server."""
    cmd = 'python compatibility_server/compatibility_checker_server.py ' \
          '--host=\'0.0.0.0\' --port=8888'
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid)
    return process


class TestCompatibilityCheckerServer(unittest.TestCase):

    def setUp(self):
        # Run application
        self.process = run_application()

        # Wait app to start
        wait_app_to_start()

    def tearDown(self):
        # Kill the flask application process
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    @retry(wait_fixed=RETRY_WAIT_PERIOD,
           stop_max_attempt_number=RETRY_MAX_ATTEMPT)
    def test_check_compatibility(self):
        response = requests.get('{}?package={}&python-version={}'.format(
            BASE_URL, PACKAGE_FOR_TEST, 3))
        status_code = response.status_code
        content = response.content.decode('utf-8')

        content_dict = ast.literal_eval(content.replace(
            'true', '"true"').replace(
            'false', '"false"').replace('null', '"null"'))

        self.assertEqual(status_code, 200)
        self.assertEqual(content_dict['packages'], [PACKAGE_FOR_TEST])
        self.assertEqual(content_dict['result'], "SUCCESS")
        self.assertIsNotNone(content_dict['dependency_info'])
