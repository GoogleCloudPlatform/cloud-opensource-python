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

from retrying import retry

import unittest

HOST_PORT = '0.0.0.0:8080'
BASE_URL = 'http://0.0.0.0:8080/'
PACKAGE_FOR_TEST = 'opencensus'

RETRY_WAIT_PERIOD = 8000 # Wait 8 seconds between each retry
RETRY_MAX_ATTEMPT = 10 # Retry 10 times

EXPECTED_SVG = open('system_test/test_data/compatibility_badge', 'rb').read()


def wait_app_to_start():
    """Wait the application to start running."""
    cmd = 'wget --retry-connrefused --tries=5 \'{}\''.format(BASE_URL)
    subprocess.check_call(cmd, shell=True)


def run_application():
    """Start running the compatibility checker server."""
    cmd = 'python badge_server/badge_server.py ' \
          '--host=\'0.0.0.0\' --port=8080'
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
        preexec_fn=os.setsid)
    return process


class TestBadgeServer(unittest.TestCase):

    def setUp(self):
        # Set the env var to run the badge server locally
        os.environ['RUN_LOCALLY'] = 'True'

        # Run application
        self.process = run_application()

        # Wait app to start
        wait_app_to_start()

    def tearDown(self):
        # Kill the application process
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    @retry(wait_fixed=RETRY_WAIT_PERIOD,
           stop_max_attempt_number=RETRY_MAX_ATTEMPT)
    def test_self_compatibility_badge(self):
        response = requests.get(
            '{}self_compatibility_badge/image?package={}'.format(
                BASE_URL, PACKAGE_FOR_TEST))
        status_code = response.status_code
        content = response.content

        self.assertEqual(status_code, 200)
        self.assertEqual(content, EXPECTED_SVG)

    @retry(wait_fixed=RETRY_WAIT_PERIOD,
           stop_max_attempt_number=RETRY_MAX_ATTEMPT)
    def test_google_compatibility_badge(self):
        response = requests.get(
            '{}google_compatibility_badge/image?package={}'.format(
                BASE_URL, PACKAGE_FOR_TEST))
        status_code = response.status_code
        content = response.content

        self.assertEqual(status_code, 200)
        self.assertEqual(content, EXPECTED_SVG)
