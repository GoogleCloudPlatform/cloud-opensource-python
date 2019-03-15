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

"""Common configs for compatibility_lib and compatibility_server.

Note that a unit test exists for checking that the configs.py file in
compatibility_lib is the same as the configs.py file in compatibility_server.

The reason for this set up is that these modules need to be isolated from
each other, but there also needs to be consistency in the objects and data
in this file since they exist in the same workflow.
"""


import enum


class PackageStatus(enum.Enum):
    """Represents a package's compatibility status

    The status is based on the results of running 'pip install' and
    'pip check' on the compatibility server

    UNKNOWN_PACKAGE: package not in whitelist
    INTERNAL_ERROR: unexpected internal error
    MISSING_DATA: missing package data from package store
    SELF_INCOMPATIBLE: pip error when installing self
    INCOMPATIBLE: pip error when installed with another package
    OUTDATED_DEPENDENCY: package has an outdated dependency
    SUCCESS: No issues
    """
    UNKNOWN_PACKAGE = 'lightgrey'
    INTERNAL_ERROR = 'lightgrey'
    MISSING_DATA = 'lightgrey'
    SELF_INCOMPATIBLE = 'red'
    INCOMPATIBLE = 'red'
    OUTDATED_DEPENDENCY = 'orange'
    SUCCESS = 'green'


def _format_url(repo_name, setuppy_path=''):
    url = 'git+git://github.com/{}.git'.format(repo_name)
    if setuppy_path != '':
        url = '{}#subdirectory={}'.format(url, setuppy_path)
    return url


# IGNORED_DEPENDENCIES are not direct dependencies for many packages and are
# not installed via pip, resulting in unresolvable high priority warnings.
IGNORED_DEPENDENCIES = [
    'pip',
    'setuptools',
    'wheel',
    'virtualenv',
]

PKG_LIST = [
    'google-api-core',
    'google-api-python-client',
    'google-auth',
    'google-cloud-asset',
    'google-cloud-automl',
    'google-cloud-bigquery',
    'google-cloud-bigquery-datatransfer',
    'google-cloud-bigtable',
    'google-cloud-container',
    'google-cloud-core',
    'google-cloud-dataproc',
    'google-cloud-datastore',
    'google-cloud-dlp',
    'google-cloud-dns',
    'google-cloud-error-reporting',
    'google-cloud-firestore',
    'google-cloud-iot',
    'google-cloud-kms',
    'google-cloud-language',
    'google-cloud-logging',
    'google-cloud-monitoring',
    'google-cloud-pubsub',
    'google-cloud-redis',
    'google-cloud-resource-manager',
    'google-cloud-runtimeconfig',
    'google-cloud-securitycenter',
    'google-cloud-spanner',
    'google-cloud-speech',
    'google-cloud-storage',
    'google-cloud-tasks',
    'google-cloud-texttospeech',
    'google-cloud-trace',
    'google-cloud-translate',
    'google-cloud-videointelligence',
    'google-cloud-vision',
    'google-cloud-websecurityscanner',
    'google-resumable-media',
    'apache-beam[gcp]',
    'google-apitools',
    'googleapis-common-protos',
    'grpc-google-iam-v1',
    'grpcio',
    'opencensus',
    'protobuf',
    'protorpc',
    'tensorboard',
    'tensorflow',
    'gcloud',
    'compatibility-lib',
]

WHITELIST_PKGS = PKG_LIST

# WHITELIST_URLS maps a github url to its associated pypi package name. This is
# used for sanitizing input packages and making sure we don't run random pypi
# or github packages.
WHITELIST_URLS = {
    _format_url('googleapis/google-cloud-python', 'asset'):
        'google-cloud-asset',
    _format_url('googleapis/google-cloud-python', 'automl'):
        'google-cloud-automl',
    _format_url('googleapis/google-cloud-python', 'dataproc'):
        'google-cloud-dataproc',
    _format_url('googleapis/google-cloud-python', 'dlp'):
        'google-cloud-dlp',
    _format_url('googleapis/google-cloud-python', 'iot'):
        'google-cloud-iot',
    _format_url('googleapis/google-cloud-python', 'kms'):
        'google-cloud-kms',
    _format_url('googleapis/python-ndb', ''):
        'google-cloud-ndb',
    # This is not released yet
    _format_url('googleapis/google-cloud-python', 'oslogin'):
        'google-cloud-os-login',
    _format_url('googleapis/google-cloud-python', 'redis'):
        'google-cloud-redis',
    _format_url('googleapis/google-cloud-python', 'securitycenter'):
        'google-cloud-securitycenter',
    _format_url('googleapis/google-cloud-python', 'tasks'):
        'google-cloud-tasks',
    _format_url('googleapis/google-cloud-python', 'texttospeech'):
        'google-cloud-texttospeech',
    _format_url('googleapis/google-cloud-python', 'websecurityscanner'):
        'google-cloud-websecurityscanner',
    _format_url('googleapis/google-cloud-python', 'api_core'):
        'google-api-core',
    _format_url('googleapis/google-cloud-python', 'bigquery'):
        'google-cloud-bigquery',
    _format_url('googleapis/google-cloud-python', 'bigquery_datatransfer'):
        'google-cloud-bigquery-datatransfer',
    _format_url('googleapis/google-cloud-python', 'bigtable'):
        'google-cloud-bigtable',
    _format_url('googleapis/google-cloud-python', 'container'):
        'google-cloud-container',
    _format_url('googleapis/google-cloud-python', 'core'):
        'google-cloud-core',
    _format_url('googleapis/google-cloud-python', 'datastore'):
        'google-cloud-datastore',
    _format_url('googleapis/google-cloud-python', 'dns'): 'google-cloud-dns',
    _format_url('googleapis/google-cloud-python', 'error_reporting'):
        'google-cloud-error-reporting',
    _format_url('googleapis/google-cloud-python', 'firestore'):
        'google-cloud-firestore',
    _format_url('googleapis/google-cloud-python', 'language'):
        'google-cloud-language',
    _format_url('googleapis/google-cloud-python', 'logging'):
        'google-cloud-logging',
    _format_url('googleapis/google-cloud-python', 'monitoring'):
        'google-cloud-monitoring',
    _format_url('googleapis/google-cloud-python', 'pubsub'):
        'google-cloud-pubsub',
    _format_url('googleapis/google-cloud-python', 'resource_manager'):
        'google-cloud-resource-manager',
    _format_url('googleapis/google-cloud-python', 'runtimeconfig'):
        'google-cloud-runtimeconfig',
    _format_url('googleapis/google-cloud-python', 'spanner'):
        'google-cloud-spanner',
    _format_url('googleapis/google-cloud-python', 'speech'):
        'google-cloud-speech',
    _format_url('googleapis/google-cloud-python', 'storage'):
        'google-cloud-storage',
    _format_url('googleapis/google-cloud-python', 'trace'):
        'google-cloud-trace',
    _format_url('googleapis/google-cloud-python', 'translate'):
        'google-cloud-translate',
    _format_url('googleapis/google-cloud-python', 'videointelligence'):
        'google-cloud-videointelligence',
    _format_url('googleapis/google-cloud-python', 'vision'):
        'google-cloud-vision',
    _format_url('googleapis/google-api-python-client'):
        'google-api-python-client',
    _format_url('googleapis/google-auth-library-python'): 'google-auth',
    _format_url('GoogleCloudPlatform/google-resumable-media-python'):
        'google-resumable-media',
    _format_url('apache/beam', 'sdks/python'): 'apache-beam[gcp]',
    _format_url('google/apitools'): 'google-apitools',
    _format_url('census-instrumentation/opencensus-python'): 'opencensus',
    _format_url('google/protorpc'): 'protorpc',
    _format_url('tensorflow/tensorflow', 'tensorflow/tools/pip_package'):
        'tensorflow',
    _format_url('GoogleCloudPlatform/cloud-opensource-python',
                'compatibility_lib'): 'compatibility-lib',
    # TODO: The following projects do not use setup.py
    # googleapis-common-protos
    # grpc-google-iam-v1
    # grpcio
    # protobuf
    # tensorboard - not sure what the build process is
    # _format_url('tensorflow/tensorboard', 'tensorboard/pip_package'):
    #     'tensorboard',
}

# TODO: Find top 30 packages by download count in BigQuery table.
THIRD_PARTY_PACKAGE_LIST = [
    'requests',
    'flask',
    'django',
]

PKG_PY_VERSION_NOT_SUPPORTED = {
    2: ['tensorflow', ],
    3: ['apache-beam[gcp]', 'gsutil', ],
}
