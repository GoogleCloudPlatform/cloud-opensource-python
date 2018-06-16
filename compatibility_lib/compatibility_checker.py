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

"""Send request to server to get self and pairwise compatibility data."""

import itertools
import concurrent.futures
import urllib.request
import json
import retrying

PKG_LIST = [
'google-api-core',
'google-api-python-client',
'google-auth',
# 'google-cloud-bigquery',
# 'google-cloud-bigquery-datatransfer',
# 'google-cloud-bigtable',
# 'google-cloud-container',
# 'google-cloud-core',
# 'google-cloud-dataflow',
# 'google-cloud-datastore',
# 'google-cloud-dns',
# 'google-cloud-error-reporting',
# 'google-cloud-firestore',
# 'google-cloud-language',
# 'google-cloud-logging',
# 'google-cloud-monitoring',
# 'google-cloud-pubsub',
# 'google-cloud-resource-manager',
# 'google-cloud-runtimeconfig',
# 'google-cloud-spanner',
# 'google-cloud-speech',
# 'google-cloud-storage',
# 'google-cloud-trace',
# 'google-cloud-translate',
# 'google-cloud-videointelligence',
# 'google-cloud-vision',
# 'google-resumable-media',
# 'cloud-utils',
# 'google-apitools',
# 'google-gax',
# 'googleapis-common-protos',
# 'grpc-google-iam-v1',
# 'grpcio',
# 'gsutil',
# 'opencensus',
# 'protobuf',
# 'protorpc',
# 'tensorboard',
# 'tensorflow',
# 'google-cloud',
# 'gcloud',
# 'oauth2client',
]

SERVER_URL = 'http://104.197.8.72'


class CompatibilityChecker(object):

    def check(self, packages, python_version):
        data = json.dumps({
            'python-version': python_version,
            'packages': packages
        }).encode('utf-8')

        check_request = urllib.request.Request(SERVER_URL, data)

        with urllib.request.urlopen(check_request) as f:
            result = json.loads(f.read().decode('utf-8'))

        return result

    @retrying.retry(wait_exponential_multiplier=5000,
                    wait_exponential_max=20000)
    def retrying_check(self, args):
        packages = args[0]
        python_version = args[1]
        return self.check(packages, python_version)

    def get_self_compatibility(self, python_version):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as p:
            pkg_set_results = p.map(
                self.retrying_check,
                (([pkg], python_version) for pkg in PKG_LIST))

            for result in zip(pkg_set_results):
                yield result

    def get_pairwise_compatibility(self, python_version):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as p:
            pkg_sets = itertools.combinations(PKG_LIST, 2)
            pkg_set_results = p.map(
                self.retrying_check,
                ((list(pkg_set), python_version) for pkg_set in pkg_sets))

            for result in zip(pkg_set_results):
                yield result
