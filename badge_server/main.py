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
"""
import datetime

import flask
import pybadges

import utils as badge_utils
from compatibility_lib import configs
from compatibility_lib import package as package_module


app = flask.Flask(__name__)


def _get_pair_status_for_packages(package_name):
    """Get the pairwise dependency compatibility check result for packages.

    Rules:
        - Return warning status if not compatible with any of the listed
          Google owned Python packages. Whole list in compatibility_lib.config.
        - Ignore the warning status if:
            - The package doesn't support one of the Python versions.
            - The package's pair is not self compatible, which means the
              pairwise conflict isn't related to the package being checked.
        - Return success status if compatible with all the list of Google owned
          Python packages.
    """
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

    pair_res = badge_utils.store.get_pairwise_compatibility_for_package(
        package_name=package_name)

    for res_list in pair_res.values():
        for res in res_list:
            py_version = badge_utils.PY_VER_MAPPING[res.python_major_version]
            # Status showing one of the check failures
            if res.status.value != 'SUCCESS':
                pkg_pair = res.packages[0].install_name \
                    if res.packages[0].install_name != package_name \
                    else res.packages[1].install_name
                # Ignore the package that not support for given py_ver
                if pkg_pair in \
                        configs.PKG_PY_VERSION_NOT_SUPPORTED.get(
                            res.python_major_version):
                    continue
                # Ignore the package that are not self compatible
                self_status = _get_self_compatibility_result(
                    package_name=pkg_pair)
                if self_status[py_version]['status'] != 'SUCCESS':
                    continue
                version_and_res[py_version]['status'] = res.status.value
                version_and_res[py_version]['details'][pkg_pair] = \
                    res.details if res.details is not None \
                    else badge_utils.EMPTY_DETAILS
    return version_and_res


def _get_self_compatibility_result(package_name):
    self_comp_res = badge_utils._build_default_result(
        status='UNKNOWN',
        details=badge_utils.PACKAGE_NOT_SUPPORTED)

    package = package_module.Package(package_name)
    compatibility_status = badge_utils.store.get_self_compatibility(
        package)

    if compatibility_status:
        for res in compatibility_status:
            py_version = badge_utils.PY_VER_MAPPING[
                res.python_major_version]
            self_comp_res[py_version]['status'] = res.status.value
            self_comp_res[py_version]['details'] = res.details \
                if res.details is not None else badge_utils.EMPTY_DETAILS

    # Add the timestamp
    self_comp_res['timestamp'] = datetime.datetime.now().strftime(
        badge_utils.TIMESTAMP_FORMAT)

    return self_comp_res


def _get_google_compatibility_result(package_name):
    google_comp_res = badge_utils._build_default_result(
        status='UNKNOWN',
        details={})

    if package_name in configs.PKG_LIST or \
                    package_name in configs.WHITELIST_URLS:
        google_comp_res = _get_pair_status_for_packages(
            package_name=package_name)

    return google_comp_res


def _get_dependency_result(package_name):
    dependency_res = {
        'status': 'UP_TO_DATE',
        'details': {},
        'timestamp': '',
    }
    details = {}
    outdated = badge_utils.highlighter.check_package(package_name)
    deprecated_deps_list = badge_utils.finder.get_deprecated_dep(
        package_name)[1]
    deprecated_deps = ', '.join(deprecated_deps_list)

    max_level = badge_utils.priority_level.UP_TO_DATE
    for dep in outdated:
        dep_detail = {}
        level = dep.priority.level
        if level.value > max_level.value:
            max_level = level
        dep_detail['installed_version'] = dep.installed_version
        dep_detail['latest_version'] = dep.latest_version
        dep_detail['priority'] = dep.priority.level.name
        dep_detail['detail'] = dep.priority.details
        details[dep.name] = dep_detail
        dependency_res['status'] = max_level.name
        dependency_res['details'] = details
        dependency_res['deprecated_deps'] = deprecated_deps
    dependency_res['timestamp'] = datetime.datetime.now().strftime(
        badge_utils.TIMESTAMP_FORMAT)

    return dependency_res


def _get_all_results(package_name):
    """Get all the check results from cache.

    Rules:
        - Return success status if all the check results are success.
        - Otherwise return warning status.
    """
    self_compat_res = _get_self_compatibility_result(
        package_name=package_name)
    google_compat_res = _get_google_compatibility_result(
        package_name=package_name)
    dependency_res = _get_dependency_result(
        package_name=package_name)

    self_res_success = self_compat_res['py2']['status'] == 'SUCCESS' or \
                       self_compat_res['py2']['status'] == 'SUCCESS'
    google_res_success = google_compat_res['py2']['status'] == 'SUCCESS' or \
                         google_compat_res['py3']['status'] == 'SUCCESS'
    dependency_res_success = dependency_res['status'] == 'UP_TO_DATE'

    if self_res_success and google_res_success and dependency_res_success:
        status = 'SUCCESS'
    else:
        status = 'CHECK_WARNING'

    # Get the latest timestamp
    self_ts = self_compat_res.get('timestamp', '')
    google_ts = google_compat_res.get('timestamp', '')
    dep_ts = dependency_res.get('timestamp', '')
    ts_list = [self_ts, google_ts, dep_ts]
    ts_list.sort(reverse=True)
    timestamp = ts_list[0] if ts_list else ''

    return status, timestamp, \
        self_compat_res, google_compat_res, dependency_res


@app.route('/')
def greetings():
    """This is for testing the server health."""
    return 'hello world'


@app.route('/one_badge_image')
def one_badge_image():
    """Generate the badge for all the checks."""
    package_name = flask.request.args.get('package')
    badge_name = flask.request.args.get('badge_name')
    is_github = False

    if badge_name is None:
        badge_name = package_name

    if 'github.com' in badge_name:
        badge_name = badge_utils.GITHUB_HEAD_NAME
        is_github = True

    # Remove the last '/' from the url root
    url_prefix = flask.request.url_root[:-1]

    status, timestamp, _, _, _ = _get_all_results(package_name)
    color = badge_utils.STATUS_COLOR_MAPPING[status]

    details_link = url_prefix + flask.url_for(
        'one_badge_target',
        package=package_name)

    # Include the check timestamp for github head
    if is_github and timestamp:
        badge_name = '{} {}'.format(badge_name, timestamp)

    response = flask.make_response(
        pybadges.badge(
            left_text=badge_name,
            right_text=status,
            right_color=color,
            whole_link=details_link))
    response.content_type = badge_utils.SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/one_badge_target')
def one_badge_target():
    package_name = flask.request.args.get('package')
    commit_number = badge_utils._calculate_commit_number(package_name)

    status, _, self_compat_res, google_compat_res, dependency_res = \
        _get_all_results(package_name)

    return flask.render_template(
        'one-badge.html',
        package_name=package_name,
        self_compat_res=self_compat_res,
        google_compat_res=google_compat_res,
        dependency_res=dependency_res,
        commit_number=commit_number)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
