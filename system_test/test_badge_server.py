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
        expected_content = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:' \
                           b'xlink="http://www.w3.org/1999/xlink" ' \
                           b'width="164" height="20"><linearGradient id="b" ' \
                           b'x2="0" y2="100%"><stop offset="0" ' \
                           b'stop-color="#bbb" stop-opacity=".1"/><stop ' \
                           b'offset="1" stop-opacity=".1"/></linearGradient>' \
                           b'<clipPath id="a"><rect width="164" height="20" ' \
                           b'rx="3" fill="#fff"/></clipPath><g clip-path=' \
                           b'"url(#a)"><path fill="#555" d="M0 0h75v20H0z"/>' \
                           b'<path fill="#007ec6" d="M75 0h89v20H75z"/>' \
                           b'<path fill="url(#b)" d="M0 0h164v20H0z"/>' \
                           b'</g><g fill="#fff" text-anchor="middle" font-' \
                           b'family="DejaVu Sans,Verdana,Geneva,sans-serif" ' \
                           b'font-size="110"> <text x="385" y="150" ' \
                           b'fill="#010101" fill-opacity=".3" transform=' \
                           b'"scale(.1)" textLength="650">opencensus</text>' \
                           b'<text x="385" y="140" transform="scale(.1)" ' \
                           b'textLength="650">opencensus</text><text ' \
                           b'x="1185" y="150" fill="#010101" fill-opacity=' \
                           b'".3" transform="scale(.1)" textLength="790">' \
                           b'CALCULATING</text><text x="1185" y="140" ' \
                           b'transform="scale(.1)" textLength="790">' \
                           b'CALCULATING</text></g> </svg>'

        self.assertEqual(status_code, 200)
        self.assertEqual(content, expected_content)
