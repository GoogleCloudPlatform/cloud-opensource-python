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
"""A HTTP server that generates badges for google python projects

Requires Python 3.6 or later.

Example usage (defaults to using host='0.0.0.0', port=8080):
    $ python3 main.py

For production usage, this module exports a WSGI application called  `app`

Supported routes:
    /one_badge_image?package=<package_name>&badge=<badge_name>
        - displays the badge image
        - lefthand side displays badge name representing a py package
        - righthand side displays the status
    /one_badge_target?package=<package_name>
        - displays self and pairwise compatibility
        - displays any outdated dependencies

Example Usage:
    http://0.0.0.0:8080/one_badge_image?package=tensorflow&badge=TensorFlow
    http://0.0.0.0:8080/one_badge_target?package=tensorflow
"""

import flask
import pybadges

import utils as badge_utils
from compatibility_lib import utils as compat_utils
from compatibility_lib import configs
from compatibility_lib import package

app = flask.Flask(__name__)


def _get_self_compatibility_dict(package_name: str) -> dict:
    """Returns a dict containing self compatibility status and details.

    Args:
        package_name: the name of the package to check (e.g.
            "google-cloud-storage").

    Returns:
        A dict containing the self compatibility status and details for any
        self incompatibilities. The dict will be formatted like the following:

        {
            'py2': { 'status': 'SUCCESS', 'details': {} },
            'py3': { 'status': 'SUCCESS', 'details': {} },
        }
    """
    pkg = package.Package(package_name)
    compatibility_results = badge_utils.store.get_self_compatibility(pkg)
    result_dict = badge_utils._build_default_result(
        status='SUCCESS',
        details='The package does not support this version of python.')
    for res in compatibility_results:
        pyver = badge_utils.PY_VER_MAPPING[res.python_major_version]
        result_dict[pyver]['status'] = res.status.value
        result_dict[pyver]['details'] = res.details
        if res.details is None:
            result_dict[pyver]['details'] = badge_utils.EMPTY_DETAILS
    return result_dict


def _get_pair_compatibility_dict(package_name: str) -> dict:
    """Get the pairwise dependency compatibility check result for a package.

    Rules:
        - Return warning status if not compatible with any of the listed
          Google owned Python packages. Whole list in compatibility_lib.config.
        - Ignore the warning status if:
            - The package doesn't support one of the Python versions.
            - The package's pair is not self compatible, which means the
              pairwise conflict isn't related to the package being checked.
        - Return success status if compatible with all the list of Google owned
          Python packages.

    Args:
        package_name: the name of the package to get pairwise dependencies for
            (e.g. "google-cloud-storage").

    Returns:
        A dict containing the pair compatibility status and details for any
        pair incompatibilities. Note that details can map to None, a string,
        or another dict. The returned dict will be formatted like the
        following:
        {
            'py2': {'status': 'INSTALL_ERROR',
                    'details': {'apache-beam[gcp]': 'NO DETAILS'}},
            'py3': {'status': 'SUCCESS', 'details': {}}
        }
    """
    result_dict = badge_utils._build_default_result(status='SUCCESS')
    pair_mapping = badge_utils.store.get_pairwise_compatibility_for_package(
        package_name)
    for pair, compatibility_results in pair_mapping.items():
        _, other_package = pair
        if package_name == other_package.install_name:
            other_package, _ = pair
        unsupported_package_mapping = configs.PKG_PY_VERSION_NOT_SUPPORTED

        for res in compatibility_results:
            version = res.python_major_version  # eg. '2', '3'
            pyver = badge_utils.PY_VER_MAPPING[version]  # eg. 'py2', 'py3'

            if result_dict[pyver]['details'] is None:
                result_dict[pyver]['details'] = {}

            # Only look at a check failure status
            # Ignore the unsupported and non self compatible packages
            if res.status.value == 'SUCCESS':
                continue

            # Not all packages are supported in both Python 2 and Python 3. If
            # `other_package` is not supported in the Python version being
            # checked then skip the result.
            unsupported_packages = unsupported_package_mapping.get(version)
            other_package_name = other_package.install_name
            if other_package_name in unsupported_packages:
                continue

            # If `other_package` is not self compatible (meaning that it has a
            # conflict within it's own dependencies) then skip the result since
            # the `other_package` will be incompatible with all other packages.
            self_compat_res = _get_self_compatibility_dict(other_package_name)
            if self_compat_res[pyver]['status'] != 'SUCCESS':
                continue

            details = res.details or badge_utils.EMPTY_DETAILS
            result_dict[pyver]['status'] = res.status.value
            result_dict[pyver]['details'][other_package_name] = details

    return result_dict


def _get_dependency_dict(package_name: str) -> dict:
    """Returns a dict containing outdated dependencies' status and details.

    Args:
        package_name: the name of the package to get outdated dependencies for
            (e.g. "google-cloud-storage").

    Returns:
        A dict containing the outdated dependency status and details for any
        outdated dependencies. Note that details maps to a dict that may be
        nested. The returned dict will be formatted like the following:
        {
            'status': 'HIGH_PRIORITY',
            'details': {
                'google-cloud-bigquery': {
                    'installed_version': '1.6.1',
                    'latest_version': '1.10.0',
                    'priority': 'HIGH_PRIORITY',
                    'detail': ('google-cloud-bigquery is 3 or more minor'
                              'versions behind the latest version')
                },
            },
        }
    """
    result_dict = badge_utils._build_default_result(
        status='UP_TO_DATE', include_pyversion=False, details={})

    outdated_deps = badge_utils.highlighter.check_package(package_name)
    _deps_list = badge_utils.finder.get_deprecated_dep(package_name)[1]
    deprecated_deps = ', '.join(_deps_list)

    outdated_depencdency_name_to_details = {}
    max_level = badge_utils.priority_level.UP_TO_DATE
    for dep in outdated_deps:
        dep_detail = {}
        level = dep.priority.level
        if level.value > max_level.value:
            max_level = level
        dep_detail['installed_version'] = dep.installed_version
        dep_detail['latest_version'] = dep.latest_version
        dep_detail['priority'] = dep.priority.level.name
        dep_detail['detail'] = dep.priority.details
        outdated_depencdency_name_to_details[dep.name] = dep_detail
    result_dict['status'] = max_level.name
    result_dict['details'] = outdated_depencdency_name_to_details
    result_dict['deprecated_deps'] = deprecated_deps

    return result_dict


def _get_badge_status(self_compat_res: dict, google_compat_res: dict,
                      dependency_res: dict) -> str:
    """Get the badge status.

    The badge status will determine the right hand text and the color of
    the badge.

    See badge_utils.STATUS_COLOR_MAPPING.
    """
    dep_status = dependency_res['status']
    dep_status = 'SUCCESS' if dep_status == 'UP_TO_DATE' else dep_status

    statuses = []
    for pyver in ['py2', 'py3']:
        statuses.append(self_compat_res[pyver]['status'])
        statuses.append(google_compat_res[pyver]['status'])
    statuses.append(dep_status)

    if all(status == 'SUCCESS' for status in statuses):
        return 'SUCCESS'
    elif 'UNKNOWN' in statuses:
        return 'UNKNOWN'
    return 'CHECK_WARNING'


def _get_check_results(package_name: str, commit_number: str = None):
    """Gets the compatibility and dependency check results.

    Returns a 3 tuple: self compatibility, pair compatibility, dependency dicts
    that are used to generate badge images and badge target pages.
    """
    self_compat_res = badge_utils._build_default_result(
        status='UNKNOWN', details={})
    google_compat_res = badge_utils._build_default_result(
        status='UNKNOWN', details={})
    dependency_res = badge_utils._build_default_result(
        status='UNKNOWN', include_pyversion=False, details={})

    # If a package is not whitelisted, return defaults
    if not compat_utils._is_package_in_whitelist([package_name]):
        return (self_compat_res, google_compat_res, dependency_res)

    self_compat_res = _get_self_compatibility_dict(package_name)
    google_compat_res = _get_pair_compatibility_dict(package_name)
    dependency_res = _get_dependency_dict(package_name)

    return (self_compat_res, google_compat_res, dependency_res)


@app.route('/')
def greetings():
    """This allows for testing server health using minimal resources"""
    return 'Hello World!'


def _format_badge_name(package_name, badge_name, commit_number):
    """Formats the badge name (assumes package_name is whitelisted)."""
    if badge_name:
        return badge_name

    if 'github.com' in package_name:
        return 'compatibility check (master)'
    else:
        return 'compatibility check (pypi)'


@app.route('/one_badge_image')
def one_badge_image():
    """Generate a badge that captures all checks."""
    package_name = flask.request.args.get('package')
    badge_name = flask.request.args.get('badge')

    commit_number = badge_utils._calculate_commit_number(package_name)
    self, google, dependency = _get_check_results(package_name)
    status = _get_badge_status(self, google, dependency)
    color = badge_utils.STATUS_COLOR_MAPPING[status]
    badge_name = _format_badge_name(package_name, badge_name, commit_number)
    details_link = '{}{}'.format(
        flask.request.url_root[:-1],
        flask.url_for('one_badge_target', package=package_name))
    badge = pybadges.badge(
        left_text=badge_name,
        right_text=status,
        right_color=color,
        whole_link=details_link)

    response = flask.make_response(badge)
    response.content_type = badge_utils.SVG_CONTENT_TYPE

    # https://tools.ietf.org/html/rfc2616#section-13.4 allows success responses
    # to be cached if no `Cache-Control` header is set. Since the content of
    # the image is frequently updated, caching is explicitly disabled to force
    # the client/cache to refetch the content on every request.
    response.headers['Cache-Control'] = 'no-cache'

    return response


@app.route('/one_badge_target')
def one_badge_target():
    package_name = flask.request.args.get('package')
    commit_number = badge_utils._calculate_commit_number(package_name)

    self, google, dependency = _get_check_results(package_name)
    target = flask.render_template(
        'one-badge.html',
        package_name=package_name,
        self_compat_res=self,
        google_compat_res=google,
        dependency_res=dependency,
        commit_number=commit_number)
    return target


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
