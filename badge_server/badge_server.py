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
'https://img.shields.io/badge/{name}-{status}-{color}.svg'
$ flask run
 * Running on http://localhost:8080/
"""
import flask
import requests
import socket

from pymemcache.client.hash import HashClient

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
_, _, ips = socket.gethostbyname_ex(
    'mycache-memcached.default.svc.cluster.local')
servers = [(ip, 11211) for ip in ips]
client = HashClient(servers, use_pooling=True)

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
}

DEP_BADGE = 'dep_badge'
SELF_COMP_BADGE = 'self_comp_badge'
GOOGLE_COMP_BADGE = 'google_comp_badge'
API_BADGE = 'api_badge'


def _get_pair_status_for_packages(pkg_sets, version_and_res):
    for pkg_set in pkg_sets:
        pkgs = [package_module.Package(pkg) for pkg in pkg_set]
        pair_res = store.get_pair_compatibility(pkgs)
        for res in pair_res:
            py_version = PY_VER_MAPPING[res.python_major_version]
            # Status showing one of the check failures
            if res.status.value != 'SUCCESS':
                version_and_res[py_version]['status'] = str(res.status.value)
                version_and_res[py_version]['details'] = str(res.details)

    return version_and_res


def _get_badge_url(version_and_res, package_name):
    # By default use the status of py3
    package_name = package_name.replace('-', '.')
    status = version_and_res['py3']['status']
    if status != 'SUCCESS':
        status = version_and_res['py2']['status']

    color = STATUS_COLOR_MAPPING[status]
    url = URL_PREFIX + '{}-{}-{}.svg'.format(
        package_name, status, color)

    return url


@app.route('/')
def greetings():
    return 'hello world'


@app.route('/dependency_badge')
def dependency_badge():
    """TODO: Badge showing whether the dependencies of a project is
    up-to-date."""
    pass


@app.route('/self_compatibility_badge/image')
def self_compatibility_badge_image():
    """Badge showing whether a package is compatible with itself."""
    package_name = flask.request.args.get('package')
    package = package_module.Package(package_name)
    compatibility_status = store.get_self_compatibility(package)

    version_and_res = {
        'py2': {
            'status': None,
            'details': None,
        },
        'py3': {
            'status': None,
            'details': None,
        }
    }

    # First see if this package is already stored in BigQuery.
    if compatibility_status:
        for res in compatibility_status:
            py_version = PY_VER_MAPPING[res.python_major_version]
            version_and_res[py_version]['status'] = res.status.value
            version_and_res[py_version]['details'] = res.details

    # If not pre stored in BigQuery, run the check for the package.
    else:
        py2_res = checker.check([package_name], '2')
        py3_res = checker.check([package_name], '3')

        version_and_res['py2']['status'] = str(py2_res.get('result'))
        version_and_res['py2']['details'] = str(py2_res.get('description'))
        version_and_res['py3']['status'] = str(py3_res.get('result'))
        version_and_res['py3']['details'] = str(py3_res.get('description'))

    url = _get_badge_url(version_and_res, package_name)

    # Write the result to cache
    client.set('{}_self_comp_badge'.format(package_name), version_and_res)

    return requests.get(url).text


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
    self_comp_res = client.get(
        '{}_self_comp_badge'.format(package_name))

    return str(self_comp_res)


@app.route('/google_compatibility_badge/image')
def google_compatibility_badge_image():
    """Badge showing whether a package is compatible with Google OSS Python
    packages. If all packages success, status is SUCCESS; else set status
    to one of the failure types, details can be found at the target link."""
    package_name = flask.request.args.get('package')

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
    pkg_sets = [[package_name, pkg] for pkg in configs.PKG_LIST]
    if package_name in configs.PKG_LIST:
        version_and_res = _get_pair_status_for_packages(
            pkg_sets, version_and_res)
    else:
        for pkg_set in pkg_sets:
            for py_ver in [2, 3]:
                py_version = PY_VER_MAPPING[py_ver]
                res = checker.check(pkg_set, str(py_ver))
                status = res.get('result')
                if status != 'SUCCESS':
                    # Status showing one of the check failures
                    version_and_res[py_version]['status'] = str(
                        res.get('result'))
                    version_and_res[py_version]['details'][pkg_set[1]] = \
                        str(res.get('description'))

    url = _get_badge_url(version_and_res, package_name)

    # Write the result to cache
    client.set('{}_google_comp_badge'.format(package_name), version_and_res)

    return requests.get(url).text


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
    google_comp_res = client.get(
        '{}_google_comp_badge'.format(package_name))

    return str(google_comp_res)


@app.route('/api_badge')
def api_badge():
    """TODO: Badge showing whether a package satisfies semantic versioning."""
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
