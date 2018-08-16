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

"""
URL for creating the badge:
[TODO] Switch to use pybadges once figure out the module not found issue.
'https://img.shields.io/badge/{name}-{status}-{color}.svg'

Commands for build the docker image and deploy to GKE:
docker build -t gcr.io/python-compatibility-tools/badge_server:v1 .
gcloud docker -- push gcr.io/python-compatibility-tools/badge_server:v1
kubectl apply -f deployment/app-with-secret.yaml
"""
import ast
import logging
import os
import requests
import threading

import flask
import redis

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import package as package_module


app = flask.Flask(__name__)

# Cache storing the package name associated with its check results.
# {
#     'pkg1_dep_badge':{},
#     'pkg1_self_comp_badge': {
#         'py2':{
#             'status': 'SUCCESS',
#             'details': None,
#         },
#         'py3':{
#             'status': 'CHECK_WARNING',
#             'details': '...',
#         }
#     },
#     'pkg1_google_comp_badge': {
#         'py2':{
#             'status': 'SUCCESS',
#             'details': None,
#         },
#         'py3':{
#             'status': 'CHECK_WARNING',
#             'details': {
#                 'package1': '...',
#             },
#         }
#     },
#     'pkg1_api_badge':{},
# }

REDIS_CACHE = {
    'opencensus_self_comp_badge': None,
    'opencensus_google_comp_badge': None,
}

def fake_redis_get(*args, **kwargs):
    key = args[2][0]
    return REDIS_CACHE[key]


def fake_redis_set(*args, **kwargs):
    key = args[2][0]
    value = str(args[2][1]).encode('utf-8')
    REDIS_CACHE[key] = value


# Patch away the redis connections if run locally
if os.environ.get('RUN_LOCALLY') is not None:
    import wrapt
    wrapt.wrap_function_wrapper('redis', 'StrictRedis.get', fake_redis_get)
    wrapt.wrap_function_wrapper('redis', 'StrictRedis.set', fake_redis_set)

redis_host = os.environ.get('REDISHOST', '10.0.0.3')
redis_port = int(os.environ.get('REDISPORT', 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port)

checker = compatibility_checker.CompatibilityChecker()
store = compatibility_store.CompatibilityStore()

URL_PREFIX = 'https://img.shields.io/badge/'

PY_VER_MAPPING = {
    2: 'py2',
    3: 'py3',
}

STATUS_COLOR_MAPPING = {
    'SUCCESS': 'green',
    'UNKNOWN': 'black',
    'INSTALL_ERROR': 'orange',
    'CHECK_WARNING': 'red',
    'CALCULATING': 'blue',
    'CONVERSION_ERROR': 'orange',
}

CONVERSION_ERROR_RES = {
    'py2': {
        'status': 'CONVERSION_ERROR',
        'details': None,
    },
    'py3': {
        'status': 'CONVERSION_ERROR',
        'details': None,
    }
}

SVG_CONTENT_TYPE = 'image/svg+xml'

EMPTY_DETAILS = 'NO DETAILS'

DEP_BADGE = 'dep_badge'
SELF_COMP_BADGE = 'self_comp_badge'
GOOGLE_COMP_BADGE = 'google_comp_badge'
API_BADGE = 'api_badge'


def _get_pair_status_for_packages(pkg_sets):
    version_and_res = {
        'py2': {
            'status': 'SUCCESS',
            'details': {},
        },
        'py3': {
            'status': 'SUCCESS',
            'details': {},
        }
    }
    for pkg_set in pkg_sets:
        pkgs = [package_module.Package(pkg) for pkg in pkg_set]
        pair_res = store.get_pair_compatibility(pkgs)
        for res in pair_res:
            py_version = PY_VER_MAPPING[res.python_major_version]
            # Status showing one of the check failures
            if res.status.value != 'SUCCESS':
                version_and_res[py_version]['status'] = res.status.value
                version_and_res[py_version]['details'][pkg_set[1]] = \
                    res.details if res.details is not None else EMPTY_DETAILS
    return version_and_res


def _get_badge_url(version_and_res, package_name):
    # By default use the status of py3, if it is not SUCCESS, and it can be
    # installed with python2, then use the result of python2.
    package_name = package_name.replace('-', '.')
    status = version_and_res['py3']['status']
    if status != 'SUCCESS' and \
            package_name not in configs.PKG_PY_VERSION_NOT_SUPPORTED.get(2):
        status = version_and_res['py2']['status']

    color = STATUS_COLOR_MAPPING[status]
    url = URL_PREFIX + '{}-{}-{}.svg'.format(
        package_name, status, color)

    return url


@app.route('/')
def greetings():
    return 'hello world'


# Endpoint for testing redis connection.
@app.route('/redis')
def index():
    value = redis_client.incr('counter', 1)
    return 'Visitor number: {}'.format(value)


@app.route('/self_compatibility_badge/image')
def self_compatibility_badge_image():
    """Badge showing whether a package is compatible with itself."""
    package_name = flask.request.args.get('package')

    version_and_res = {
        'py2': {
            'status': 'CALCULATING',
            'details': None,
        },
        'py3': {
            'status': 'CALCULATING',
            'details': None,
        }
    }

    def run_check():
        # First see if this package is already stored in BigQuery.
        package = package_module.Package(package_name)
        compatibility_status = store.get_self_compatibility(package)
        if compatibility_status:
            for res in compatibility_status:
                py_version = PY_VER_MAPPING[res.python_major_version]
                version_and_res[py_version]['status'] = res.status.value
                version_and_res[py_version]['details'] = res.details \
                    if res.details is not None else EMPTY_DETAILS

        # If not pre stored in BigQuery, run the check for the package.
        else:
            py2_res = checker.check([package_name], '2')
            py3_res = checker.check([package_name], '3')

            version_and_res['py2']['status'] = py2_res.get('result')
            py2_description = py2_res.get('description')
            py2_details = EMPTY_DETAILS if py2_description is None \
                else py2_description
            version_and_res['py2']['details'] = py2_details
            version_and_res['py3']['status'] = py3_res.get('result')
            py3_description = py3_res.get('description')
            py3_details = EMPTY_DETAILS if py3_description is None \
                else py3_description
            version_and_res['py3']['details'] = py3_details

        url = _get_badge_url(version_and_res, package_name)

        # Write the result to memory store
        redis_client.set(
            '{}_self_comp_badge'.format(package_name), version_and_res)
        return requests.get(url).text

    self_comp_res = redis_client.get(
        '{}_self_comp_badge'.format(package_name))
    threading.Thread(target=run_check).start()

    if self_comp_res is not None:
        try:
            details = ast.literal_eval(self_comp_res.decode('utf-8'))
        except SyntaxError:
            logging.error(
                'Error occurs while converting to dict, value is {}.'.format(
                    self_comp_res))
            details = CONVERSION_ERROR_RES
    else:
        details = version_and_res

    url = _get_badge_url(details, package_name)
    response = flask.make_response(requests.get(url).text)
    response.content_type = SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/self_compatibility_badge/target')
def self_compatibility_badge_target():
    """Return the dict which contains the self compatibility status and details
    for py2 and py3.

    e.g. {
          'py2':{
              'status': 'SUCCESS',
              'details': None,
          },
          'py3':{
              'status': 'CHECK_WARNING',
              'details': '...',
          }
      }
    """
    package_name = flask.request.args.get('package')
    self_comp_res = redis_client.get(
        '{}_self_comp_badge'.format(package_name))

    return str(self_comp_res)


@app.route('/google_compatibility_badge/image')
def google_compatibility_badge_image():
    """Badge showing whether a package is compatible with Google OSS Python
    packages. If all packages success, status is SUCCESS; else set status
    to one of the failure types, details can be found at the target link."""
    package_name = flask.request.args.get('package')

    default_version_and_res = {
        'py2': {
            'status': 'CALCULATING',
            'details': {},
        },
        'py3': {
            'status': 'CALCULATING',
            'details': {},
        }
    }

    def run_check():
        pkg_sets = [[package_name, pkg] for pkg in configs.PKG_LIST]
        if package_name in configs.PKG_LIST:
            result = _get_pair_status_for_packages(pkg_sets)
        else:
            for pkg_set in pkg_sets:
                for py_ver in [2, 3]:
                    py_version = PY_VER_MAPPING[py_ver]
                    res = checker.check(pkg_set, str(py_ver))
                    status = res.get('result')
                    if status != 'SUCCESS':
                        # Ignore the package that not support for given py_ver
                        if pkg_set[1] in \
                                configs.PKG_PY_VERSION_NOT_SUPPORTED.get(
                                py_ver):
                            continue
                        # Status showing one of the check failures
                        default_version_and_res[
                            py_version]['status'] = res.get('result')
                        description = res.get('description')
                        details = EMPTY_DETAILS if description is None \
                            else description
                        default_version_and_res[
                            py_version]['details'][pkg_set[1]] = details
            result = default_version_and_res

        # Write the result to memory store
        redis_client.set(
            '{}_google_comp_badge'.format(package_name), result)
        url = _get_badge_url(result, package_name)
        return requests.get(url).text

    google_comp_res = redis_client.get(
        '{}_google_comp_badge'.format(package_name))
    threading.Thread(target=run_check).start()

    if google_comp_res is not None:
        try:
            details = ast.literal_eval(google_comp_res.decode('utf-8'))
        except SyntaxError:
            logging.error(
                'Error occurs while converting to dict, value is {}.'.format(
                    google_comp_res))
            details = CONVERSION_ERROR_RES
    else:
        details = default_version_and_res

    url = _get_badge_url(details, package_name)
    response = flask.make_response(requests.get(url).text)
    response.content_type = SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/google_compatibility_badge/target')
def google_compatibility_badge_target():
    """Return the dict which contains the compatibility status with google
    packages and details for py2 and py3.

        e.g. {
              'py2':{
                  'status': 'SUCCESS',
                  'details': None,
              },
              'py3':{
                  'status': 'CHECK_WARNING',
                  'details': {
                      'package1': '...',
                  },
              }
          }
    """
    package_name = flask.request.args.get('package')
    google_comp_res = redis_client.get(
        '{}_google_comp_badge'.format(package_name))

    return str(google_comp_res)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
