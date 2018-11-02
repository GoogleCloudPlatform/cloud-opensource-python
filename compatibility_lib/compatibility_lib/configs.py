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

"""Common configs for compatibility_lib."""


# IGNORED_DEPENDENCIES are not direct dependencies for many packages and are
# not installed via pip, resulting in unresolvable high priority warnings.
IGNORED_DEPENDENCIES = [
    'pip',
    'setuptools',
    'wheel',
]

PKG_LIST = [
    'google-api-core',
    'google-api-python-client',
    'google-auth',
    'google-cloud-bigquery',
    'google-cloud-bigquery-datatransfer',
    'google-cloud-bigtable',
    'google-cloud-container',
    'google-cloud-core',
    'google-cloud-datastore',
    'google-cloud-dns',
    'google-cloud-error-reporting',
    'google-cloud-firestore',
    'google-cloud-language',
    'google-cloud-logging',
    'google-cloud-monitoring',
    'google-cloud-pubsub',
    'google-cloud-resource-manager',
    'google-cloud-runtimeconfig',
    'google-cloud-spanner',
    'google-cloud-speech',
    'google-cloud-storage',
    'google-cloud-trace',
    'google-cloud-translate',
    'google-cloud-videointelligence',
    'google-cloud-vision',
    'google-resumable-media',
    'apache-beam[gcp]',
    'google-apitools',
    'googleapis-common-protos',
    'grpc-google-iam-v1',
    'grpcio',
    'gsutil',
    'opencensus',
    'protobuf',
    'protorpc',
    'tensorboard',
    'tensorflow',
    'gcloud',
]

# TODO: Find top 30 packages by download count in BigQuery table.
THIRD_PARTY_PACKAGE_LIST = [
    'requests',
    'flask',
    'django',
]

PKG_PY_VERSION_NOT_SUPPORTED = {
    2: ['tensorflow', ],
    3: ['google-cloud-dataflow', ],
}
