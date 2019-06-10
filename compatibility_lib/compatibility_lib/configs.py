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

Steps for updating the package list / white list:
    1. Make sure to update both lists when appropriate (the package has been
    release to PyPI and the github repo exists)
    2. Skip the dashboard tests and build when adding any new packages to
    either list
    3. Release a new version of compatibility lib
    4. Redeploy the compatibility server
    5. Unskip the dashboard tests and build
"""


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

# If updating this list, make sure to update the whitelist as well with the
# appropiate github repo if one exists.
PKG_LIST = [
    'google-api-core',
    'google-api-python-client',
    'google-auth',
    'google-cloud-asset',
    'google-cloud-automl',
    'google-cloud-bigquery',
    'google-cloud-bigquery-datatransfer',
    'google-cloud-bigquery-storage',
    'google-cloud-bigtable',
    'google-cloud-container',
    'google-cloud-core',
    'google-cloud-datacatalog',
    'google-cloud-datalabeling',
    'google-cloud-dataproc',
    'google-cloud-datastore',
    'google-cloud-dlp',
    'google-cloud-dns',
    'google-cloud-error-reporting',
    'google-cloud-firestore',
    'google-cloud-iam',
    'google-cloud-iot',
    # 'google-cloud-irm', # unreleased
    'google-cloud-kms',
    'google-cloud-language',
    'google-cloud-logging',
    'google-cloud-monitoring',
    'google-cloud-os-login',
    # 'google-cloud-phishing-protection', # unreleased
    'google-cloud-pubsub',
    'google-cloud-redis',
    'google-cloud-resource-manager',
    'google-cloud-runtimeconfig',
    'google-cloud-scheduler',
    'google-cloud-securitycenter',
    'google-cloud-spanner',
    'google-cloud-speech',
    'google-cloud-storage',
    'google-cloud-talent',
    'google-cloud-tasks',
    'google-cloud-texttospeech',
    'google-cloud-trace',
    'google-cloud-translate',
    'google-cloud-videointelligence',
    'google-cloud-vision',
    'google-cloud-webrisk',
    'google-cloud-websecurityscanner',
    'google-resumable-media',
    'apache-beam[gcp]',
    'google-apitools',
    'googleapis-common-protos',
    'grpc-google-iam-v1',
    'grpcio',
    'opencensus',
    'opencensus-correlation',
    'opencensus-ext-azure',
    'opencensus-ext-dbapi',
    'opencensus-ext-django',
    'opencensus-ext-flask',
    'opencensus-ext-gevent',
    'opencensus-ext-google-cloud-clientlibs',
    'opencensus-ext-grpc',
    'opencensus-ext-httplib',
    'opencensus-ext-jaeger',
    'opencensus-ext-logging',
    'opencensus-ext-mysql',
    'opencensus-ext-ocagent',
    'opencensus-ext-postgresql',
    'opencensus-ext-prometheus',
    'opencensus-ext-pymongo',
    'opencensus-ext-pymysql',
    'opencensus-ext-pyramid',
    'opencensus-ext-requests',
    'opencensus-ext-sqlalchemy',
    'opencensus-ext-stackdriver',
    'opencensus-ext-threading',
    'opencensus-ext-zipkin',
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
# If updating this list, make sure to update the `PKG_LIST` with the
# appropriate pypi package if one has been released.
WHITELIST_URLS = {
    _format_url('googleapis/google-cloud-python', 'asset'):
        'google-cloud-asset',
    _format_url('googleapis/google-cloud-python', 'automl'):
        'google-cloud-automl',
    _format_url('googleapis/google-cloud-python', 'datacatalog'):
        'google-cloud-datacatalog',
    _format_url('googleapis/google-cloud-python', 'datalabeling'):
        'google-cloud-datalabeling',
    _format_url('googleapis/google-cloud-python', 'dataproc'):
        'google-cloud-dataproc',
    _format_url('googleapis/google-cloud-python', 'dlp'):
        'google-cloud-dlp',
    _format_url('googleapis/google-cloud-python', 'iam'):
        'google-cloud-iam',
    _format_url('googleapis/google-cloud-python', 'iot'):
        'google-cloud-iot',
    # unreleased
    _format_url('googleapis/google-cloud-python', 'irm'):
        'google-cloud-irm',
    _format_url('googleapis/google-cloud-python', 'kms'):
        'google-cloud-kms',
    _format_url('googleapis/python-ndb', ''):
        'google-cloud-ndb',
    _format_url('googleapis/google-cloud-python', 'oslogin'):
        'google-cloud-os-login',
    _format_url('googleapis/google-cloud-python', 'redis'):
        'google-cloud-redis',
    _format_url('googleapis/google-cloud-python', 'scheduler'):
        'google-cloud-scheduler',
    _format_url('googleapis/google-cloud-python', 'securitycenter'):
        'google-cloud-securitycenter',
    _format_url('googleapis/google-cloud-python', 'tasks'):
        'google-cloud-tasks',
    _format_url('googleapis/google-cloud-python', 'texttospeech'):
        'google-cloud-texttospeech',
    _format_url('googleapis/google-cloud-python', 'webrisk'):
        'google-cloud-webrisk',
    _format_url('googleapis/google-cloud-python', 'websecurityscanner'):
        'google-cloud-websecurityscanner',
    _format_url('googleapis/google-cloud-python', 'api_core'):
        'google-api-core',
    _format_url('googleapis/google-cloud-python', 'bigquery'):
        'google-cloud-bigquery',
    _format_url('googleapis/google-cloud-python', 'bigquery_datatransfer'):
        'google-cloud-bigquery-datatransfer',
    _format_url('googleapis/google-cloud-python', 'bigquery_storage'):
        'google-cloud-bigquery-storage',
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
    # unreleased
    _format_url('googleapis/google-cloud-python', 'phishingprotection'):
        'google-cloud-phishing-protection',
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
    _format_url('googleapis/google-cloud-python', 'talent'):
        'google-cloud-talent',
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
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-correlation'): 'opencensus-correlation',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-azure'): 'opencensus-ext-azure',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-dbapi'): 'opencensus-ext-dbapi',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-django'): 'opencensus-ext-django',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-flask'): 'opencensus-ext-flask',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-gevent'): 'opencensus-ext-gevent',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-google-cloud-clientlibs'):
        'opencensus-ext-google-cloud-clientlibs',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-grpc'): 'opencensus-ext-grpc',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-httplib'): 'opencensus-ext-httplib',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-jaeger'): 'opencensus-ext-jaeger',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-logging'): 'opencensus-ext-logging',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-mysql'): 'opencensus-ext-mysql',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-ocagent'): 'opencensus-ext-ocagent',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-postgresql'):
        'opencensus-ext-postgresql',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-prometheus'):
        'opencensus-ext-prometheus',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-pymongo'): 'opencensus-ext-pymongo',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-pymysql'): 'opencensus-ext-pymysql',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-pyramid'): 'opencensus-ext-pyramid',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-requests'): 'opencensus-ext-requests',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-sqlalchemy'):
        'opencensus-ext-sqlalchemy',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-stackdriver'):
        'opencensus-ext-stackdriver',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-threading'):
        'opencensus-ext-threading',
    _format_url('census-instrumentation/opencensus-python',
                'contrib/opencensus-ext-zipkin'): 'opencensus-ext-zipkin',
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
