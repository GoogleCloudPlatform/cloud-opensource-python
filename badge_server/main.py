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

"""A HTTP server for badges"""

import datetime
import flask
import pybadges

import utils as badge_utils
from compatibility_lib import utils as compat_utils
from compatibility_lib import configs
from compatibility_lib import package

app = flask.Flask(__name__)


def _get_self_compatibility_result_dict(pkgname) -> dict:
    """Return the dict which contains the self compatibility status and details
    for py2 and py3.
    """
    pkg = package.Package(pkgname)
    compatibility_results = badge_utils.store.get_self_compatibility(pkg)
    result_dict = badge_utils._build_default_result(
        badge_type=badge_utils.BadgeType.SELF_COMP_BADGE,
        status='SUCCESS',
        details='The package does not support this version of python.')
    for res in compatibility_results:
        pyver = badge_utils.PY_VER_MAPPING[res.python_major_version]
        result_dict[pyver]['status'] = res.status.value
        result_dict[pyver]['details'] = res.details
        if res.details is None:
            result_dict[pyver]['details'] = badge_utils.EMPTY_DETAILS
    return result_dict


def _get_pair_compatibility_result_dict(pkgname) -> dict:
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
    """
    result_dict = badge_utils._build_default_result(
        badge_type=badge_utils.BadgeType.GOOGLE_COMP_BADGE, status='SUCCESS')

    pkg_pairs = [[package.Package(pkgname), package.Package(pkg)]
                 for pkg in configs.PKG_LIST]
    for pair in pkg_pairs:
        _, other_pkg = pair
        compatibility_results = badge_utils.store.get_pair_compatibility(pair)

        for res in compatibility_results:
            ver = res.python_major_version            # eg. '2', '3'
            pyver = badge_utils.PY_VER_MAPPING[ver]   # eg. 'py2', 'py3'

            if result_dict[pyver]['details'] is None:
                result_dict[pyver]['details'] = {}

            # Only look at a check failure status
            # Ignore the unsupported and non self compatible packages
            if res.status.value == 'SUCCESS':
                continue
            unsupported_pkgs = configs.PKG_PY_VERSION_NOT_SUPPORTED.get(ver)
            if other_pkg in unsupported_pkgs:
                continue
            self_compat_res = _get_self_compatibility_result_dict(
                other_pkg.install_name)
            if self_compat_res[pyver]['status'] != 'SUCCESS':
                continue

            details = res.details if res.details else badge_utils.EMPTY_DETAILS
            result_dict[pyver]['status'] = res.status.value
            result_dict[pyver]['details'][other_pkg] = details

    return result_dict


def _get_dependency_result_dict(pkgname) -> dict:
    """Return the dict which contains the self outdated dependencies
    status and details.
    """
    result_dict = badge_utils._build_default_result(
        badge_utils.BadgeType.DEP_BADGE, 'UP_TO_DATE', {})

    outdated_deps = badge_utils.highlighter.check_package(pkgname)
    _deps_list = badge_utils.finder.get_deprecated_dep(pkgname)[1]
    deprecated_deps = ', '.join(_deps_list)

    details = {}
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
        details[dep.name] = dep_detail
        result_dict['status'] = max_level.name
        result_dict['details'] = details
        result_dict['deprecated_deps'] = deprecated_deps

    result_dict['timestamp'] = datetime.datetime.now().strftime(
        badge_utils.TIMESTAMP_FORMAT)

    return result_dict


def _get_status(
        self_compat_res: dict,
        google_compat_res: dict,
        dependency_res: dict) -> str:
    """Get the cummulative status"""
    dep_status = dependency_res['status']
    dep_status = 'SUCCESS' if dep_status == 'UP_TO_DATE' else dep_status

    _statuses = []
    for pyver in ['py2', 'py3']:
        _statuses.append(self_compat_res[pyver]['status'])
        _statuses.append(google_compat_res[pyver]['status'])
    _statuses.append(dep_status)

    if ['SUCCESS'] * len(_statuses) == _statuses:
        return 'SUCCESS'
    elif 'CALCULATING' in _statuses:
        return 'CALCULATING'
    elif 'UNKNOWN' in _statuses:
        return 'UNKNOWN'
    return 'CHECK_WARNING'


def _get_timestamp(
        self_compat_res: dict,
        google_compat_res: dict,
        dependency_res: dict) -> str:
    """Get the timestamp"""
    self_compat_ts = self_compat_res.get('timestamp', '')
    google_compat_ts = google_compat_res.get('timestamp', '')
    dependency_ts = dependency_res.get('timestamp', '')
    ts_list = [self_compat_ts, google_compat_ts, dependency_ts]
    ts_list.sort(reverse=True)
    timestamp = ts_list[0] if ts_list else ''
    return timestamp


def _get_results_from_compatibility_store(
        pkgname: str,
        commit_number: str = None):
    """Gets the status and timestamp"""
    if not compat_utils._is_package_in_whitelist([pkgname]):
        return ('UNKNOWN', '', {}, {}, {})

    self_compat_res = _get_self_compatibility_result_dict(pkgname)
    google_compat_res = _get_pair_compatibility_result_dict(pkgname)
    dependency_res = _get_dependency_result_dict(pkgname)

    status = _get_status(self_compat_res, google_compat_res, dependency_res)
    timestamp = _get_timestamp(
        self_compat_res, google_compat_res, dependency_res)

    return (status, timestamp, self_compat_res, google_compat_res,
            dependency_res)


@app.route('/')
def greetings():
    """This allows for testing server health using minimal resources"""
    return 'Hello World!'


def _format_badge_name(pkgname, bdgname, commit_number):
    """Formats the badge name based on a number of factors.
    This function assumes that the pkgname is whitelisted.
    """
    if bdgname is None:
        bdgname = pkgname

    # TODO: implement checks for the following conditions
    # (they are currently using dummy info)
    is_pypi = compat_utils._is_package_in_whitelist([pkgname])
    is_latest_commit = True
    if 'github.com' in pkgname:
        parens_text = 'master' if is_latest_commit else 'updating...'
        bdgname = '{} ({})'.format(bdgname, parens_text)
    elif is_pypi:
        bdgname = '{} (PyPI)'.format(bdgname)

    return bdgname


@app.route('/one_badge_image')
def one_badge_image():
    """Generate a badge that captures all checks."""
    pkgname = flask.request.args.get('package')
    bdgname = flask.request.args.get('badge')

    commit_number = badge_utils._calculate_commit_number(pkgname)
    status, timestamp, _, _, _ = _get_results_from_compatibility_store(pkgname)
    color = badge_utils.STATUS_COLOR_MAPPING[status]
    bdgname = _format_badge_name(pkgname, bdgname, commit_number)
    details_link = '{}{}'.format(
        flask.request.url_root[:-1],
        flask.url_for('one_badge_target', package=pkgname))
    badge = pybadges.badge(
        left_text=bdgname,
        right_text=status,
        right_color=color,
        whole_link=details_link)

    response = flask.make_response(badge)
    response.content_type = badge_utils.SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()
    return response


@app.route('/one_badge_target')
def one_badge_target():
    pkgname = flask.request.args.get('package')
    commit_number = badge_utils._calculate_commit_number(pkgname)

    status, _, self, google, dep = _get_results_from_compatibility_store(
        pkgname)
    return flask.render_template(
        'one-badge.html',
        package_name=pkgname,
        self_compat_res=self,
        google_compat_res=google,
        dependency_res=dep,
        commit_number=commit_number)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
