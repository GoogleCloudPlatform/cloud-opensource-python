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
 * Running on http://127.0.0.1:5000/
"""
import flask
import requests

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import package as package_module

app = flask.Flask(__name__)

checker = compatibility_checker.CompatibilityChecker()
store = compatibility_store.CompatibilityStore()

URL_PREFIX = 'https://img.shields.io/badge/'

STATUS_COLOR_MAPPING = {
    'SUCCESS': 'green',
    'UNKNOWN': 'grey',
    'INSTALL_ERROR': 'orange',
    'CHECK_WARNING': 'red',
}


def _get_pair_status_for_packages(pkg_sets):
    version_status = {2: 'SUCCESS', 3: 'SUCCESS'}
    for pkg_set in pkg_sets:
        pkgs = [package_module.Package(pkg) for pkg in pkg_set]
        pair_res = store.get_pair_compatibility(pkgs)
        for res in pair_res:
            status = res.status.value
            if status != 'SUCCESS':
                version_status[res.python_major_version] = status

    res = None
    for value in version_status.values():
        if value == 'SUCCESS':
            return value
        else:
            res = value

    return res


@app.route('/dependency_badge')
def dependency_badge():
    """(TODO) Badge showing whether the dependencies of a project is
    up-to-date."""
    pass


@app.route('/self_compatibility_badge')
def self_compatibility_badge():
    """Badge showing whether a package is compatible with itself."""
    package_name = flask.request.args.get('package')
    package = package_module.Package(package_name)
    compatibility_status = store.get_self_compatibility(package)

    # First see if this package is already stored in BigQuery.
    if compatibility_status:
        for res in compatibility_status:
            # We mark the status as success either py2 or py3 success
            if res.status.value == 'SUCCESS':
                status = res.status
                color = STATUS_COLOR_MAPPING[status.value]
                break
    # If not pre stored in BigQuery, run the check for the package.
    else:
        # By default use the status of py3
        res = checker.check([package_name], '3')
        status = res.get('result')
        if status != 'SUCCESS':
            res = checker.check([package_name], '2')
        status = res.get('result')
        color = STATUS_COLOR_MAPPING[status]

    url = URL_PREFIX + '{}-{}-{}.svg'.format(
        package_name, status, color)

    return requests.get(url).text


@app.route('/google_compatibility_badge')
def google_compatibility_badge():
    """Badge showing whether a package is compatible with Google OSS Python
    packages"""
    package_name = flask.request.args.get('package')

    status = None
    if package_name in configs.PKG_LIST:
        pkg_sets = [[package_name, pkg] for pkg in configs.PKG_LIST]
        status = _get_pair_status_for_packages(pkg_sets)
    else:
        # (TODO): Run the check if package not in PKG_LIST
        pass

    color = STATUS_COLOR_MAPPING[status]

    url = URL_PREFIX + '{}-{}-{}.svg'.format(
        package_name, status, color)

    return requests.get(url).text


@app.route('/api_badge')
def api_badge():
    """(TODO) Badge showing whether a package satisfies semantic versioning."""
    pass


if __name__ == '__main__':
    app.run(host='localhost', port=8080)
