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

import enum
import flask
import logging
import pybadges

import utils as badge_utils
from compatibility_lib import utils as compat_utils
from compatibility_lib import dependency_highlighter as highlighter

from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import package
from typing import FrozenSet, Iterable, List, Optional

app = flask.Flask(__name__)


@enum.unique
class BadgeStatus(enum.Enum):
    """Represents a package's badge status.

    The status is based on the results of running 'pip install' and
    'pip check' on the compatibility server. Statuses are defined in
    descending priority level.

    UNKNOWN_PACKAGE: package not in whitelist
    INTERNAL_ERROR: unexpected internal error
    MISSING_DATA: missing package data from package store
    SELF_INCOMPATIBLE: pip error when installing self
    PAIR_INCOMPATIBLE: pip error when installed with another package
    OBSOLETE_DEPENDENCY: package has a high priority outdated dependency
    OUTDATED_DEPENDENCY: package has a low priority outdated dependency
    SUCCESS: No issues
    """
    UNKNOWN_PACKAGE = 'unknown package'
    INTERNAL_ERROR = 'internal error'
    MISSING_DATA = 'missing data'
    SELF_INCOMPATIBLE = 'self incompatible'
    PAIR_INCOMPATIBLE = 'incompatible'
    OBSOLETE_DEPENDENCY = 'obsolete dependency'
    OUTDATED_DEPENDENCY = 'old dependency'
    SUCCESS = 'success'

    @classmethod
    def get_highest_status(cls, statuses: Iterable[enum.Enum]):
        """Gets the highest BadgeStatus.

        This method works because `cls.__members__` is an ordered dict.

        Args:
            statuses: A list of BadgeStatuses.

        Returns:
            The BadgeStatus found in `statuses` that has the highest priority.
            For example, INTERNAL_ERROR would be returned if `statuses`
            contained INTERNAL_ERROR and OUTDATED_DEPENDENCY.

        Raises:
            ValueError: If no BadgeStatus exists. For example, if the length of
                `statuses` is 0, an error is raised.
        """
        for status in cls.__members__.values():
            if status in statuses:
                return status
        raise ValueError("'statuses' did not contain a valid BadgeStatus")


BADGE_STATUS_TO_COLOR = {
    BadgeStatus.UNKNOWN_PACKAGE: 'lightgrey',
    BadgeStatus.INTERNAL_ERROR: 'lightgrey',
    BadgeStatus.MISSING_DATA: 'lightgrey',
    BadgeStatus.SELF_INCOMPATIBLE: 'red',
    BadgeStatus.PAIR_INCOMPATIBLE: 'red',
    BadgeStatus.OBSOLETE_DEPENDENCY: 'red',
    BadgeStatus.OUTDATED_DEPENDENCY: 'yellowgreen',
    BadgeStatus.SUCCESS: 'brightgreen',
}


# Note: An INSTALL_ERROR occurs when pip_check yields an
# PipCheckResultType.INSTALL_ERROR. Technically, this could happen when
# querying the compatibility server if the input had an unrecognized package
# or a given package does not support the given python version, both of which
# are not internal errors. However, since we handle for those cases, we should
# never get an INSTALL_ERROR for either of those reasons. An INSTALL_ERROR
# *could* occur when a github repo subdirectory is moved or some error is
# thrown in code.
PACKAGE_STATUS_TO_BADGE_STATUS = {
    compatibility_store.Status.UNKNOWN: BadgeStatus.UNKNOWN_PACKAGE,
    compatibility_store.Status.SUCCESS: BadgeStatus.SUCCESS,
    compatibility_store.Status.INSTALL_ERROR: BadgeStatus.INTERNAL_ERROR,
    compatibility_store.Status.CHECK_WARNING: None
}


DEPENDENCY_STATUS_TO_BADGE_STATUS = {
    highlighter.PriorityLevel.UP_TO_DATE: BadgeStatus.SUCCESS,
    highlighter.PriorityLevel.LOW_PRIORITY: BadgeStatus.OUTDATED_DEPENDENCY,
    highlighter.PriorityLevel.HIGH_PRIORITY: BadgeStatus.OBSOLETE_DEPENDENCY,
}


def _get_missing_details(package_names: List[str],
                         results: Iterable[
                             compatibility_store.CompatibilityResult]
                         ) -> Optional[str]:
    """Gets the details for any missing data (if there is any)

    Args:
        package_names: A list of length 1 or 2 of the package name(s) to look
            up, e.g. ["tensorflow"], ["tensorflow", "opencensus"].
        results: A list of length 1 or 2 of the `CompatibilityResults` for the
            given package(s). The package names in the `CompatibilityResults`
            should match the package_names argument.

    Returns:
        None if there is no missing data; a description of the package(s) and
        version(s) missing otherwise.
        For example, if package_names=['opencensus'], and given that
        `opencensus` is compatible with both python versions 2 and 3, if
        `results` only contained a result for 3, this would be returned:
        "Missing data for packages=['opencensus'], versions=[2]".
    """
    message = 'package_names: Expected length of 1 or 2, got {}'.format(
        len(package_names))
    assert len(package_names) in (1, 2), message

    message = 'One of the packages in {} is not whitelisted'.format(
        str(package_names))
    assert compat_utils._is_package_in_whitelist(package_names), message

    all_versions = (2, 3)
    versions_supported = set(all_versions)
    for version in all_versions:
        for package_name in package_names:
            if 'github.com' in package_name:
                package_name = configs.WHITELIST_URLS[package_name]
            if package_name in configs.PKG_PY_VERSION_NOT_SUPPORTED[version]:
                versions_supported.discard(version)
                break

    versions_seen = {result.python_major_version for result in results}

    if versions_seen.issuperset(versions_supported):
        return None

    missing_versions = list(versions_supported - versions_seen)
    missing_details = 'Missing data for packages={}, versions={}'.format(
        package_names, missing_versions)
    return missing_details


def _get_self_compatibility_dict(package_name: str) -> dict:
    """Returns a dict containing self compatibility status and details.

    Args:
        package_name: the name of the package to check (e.g.
            "google-cloud-storage").

    Returns:
        A dict containing the self compatibility status and details for any
        self incompatibilities. The dict will be formatted like the following:

        {
            'py2': { 'status': BadgeStatus.SUCCESS, 'details': {} },
            'py3': { 'status': BadgeStatus.SUCCESS, 'details': {} },
        }
    """
    pkg = package.Package(package_name)
    compatibility_results = badge_utils.store.get_self_compatibility(pkg)
    missing_details = _get_missing_details(
        [package_name], compatibility_results)
    if missing_details:
        result_dict = badge_utils._build_default_result(
            status=BadgeStatus.MISSING_DATA, details=missing_details)
        return result_dict

    result_dict = badge_utils._build_default_result(
        status=BadgeStatus.SUCCESS,
        details='The package does not support this version of python.')
    for res in compatibility_results:
        pyver = badge_utils.PY_VER_MAPPING[res.python_major_version]
        badge_status = PACKAGE_STATUS_TO_BADGE_STATUS.get(
            res.status) or BadgeStatus.SELF_INCOMPATIBLE
        result_dict[pyver]['status'] = badge_status
        result_dict[pyver]['details'] = res.details
        if res.details is None:
            result_dict[pyver]['details'] = badge_utils.EMPTY_DETAILS
    return result_dict


def _get_other_package_from_set(name: str,
                                package_set: FrozenSet[package.Package]
                                ) -> package.Package:
    """Returns the package that does *not* have the given name.

    Args:
        name: The name of the package not to return.
        package_set: A set of two unsorted packages, one of which has the
            given name.

    Returns:
        The Package object that doesn't correspond to the give package name.
    """
    first, second = package_set
    if first.install_name == name:
        return second
    return first


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
        pair incompatibilities. Note that details must map to another dict.
        The returned dict will be formatted like the
        following:
        {
            'py2': {'status': BadgeStatus.PAIR_INCOMPATIBLE,
                    'details': {'apache-beam[gcp]': 'NO DETAILS'}},
            'py3': {'status': BadgeStatus.SUCCESS, 'details': {}}
        }
    """
    default_details = {}
    result_dict = badge_utils._build_default_result(
        status=BadgeStatus.SUCCESS, details=default_details)
    unsupported_package_mapping = configs.PKG_PY_VERSION_NOT_SUPPORTED
    pair_mapping = badge_utils.store.get_pairwise_compatibility_for_package(
        package_name)
    for pair, compatibility_results in pair_mapping.items():
        missing_details = _get_missing_details(
            [pkg.install_name for pkg in pair], compatibility_results)
        if missing_details:
            result_dict = badge_utils._build_default_result(
                status=BadgeStatus.MISSING_DATA, details=missing_details)
            return result_dict

        other_package = _get_other_package_from_set(package_name, pair)

        for res in compatibility_results:
            version = res.python_major_version            # eg. '2', '3'
            pyver = badge_utils.PY_VER_MAPPING[version]   # eg. 'py2', 'py3'

            if result_dict[pyver]['details'] is default_details:
                result_dict[pyver]['details'] = {}

            # Not all packages are supported in both Python 2 and Python 3. If
            # either package is not supported in the Python version being
            # checked then skip the check.
            unsupported_packages = unsupported_package_mapping.get(version)
            if any([pkg.install_name in unsupported_packages for pkg in pair]):
                continue

            # The logic after this point only handles non SUCCESS statuses.
            if res.status == compatibility_store.Status.SUCCESS:
                continue

            # If `other_package` is not self compatible (meaning that it has a
            # conflict within it's own dependencies) then skip the check since
            # a pairwise comparison is only significant if both packages are
            # self_compatible.
            other_package_name = other_package.install_name
            self_compat_res = _get_self_compatibility_dict(other_package_name)
            if self_compat_res[pyver]['status'] != BadgeStatus.SUCCESS:
                continue

            details = res.details or badge_utils.EMPTY_DETAILS
            badge_status = PACKAGE_STATUS_TO_BADGE_STATUS.get(
                res.status) or BadgeStatus.PAIR_INCOMPATIBLE
            result_dict[pyver]['status'] = badge_status
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
            'status': BadgeStatus.OBSOLETE_DEPENDENCY,
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
        status=BadgeStatus.SUCCESS, include_pyversion=False, details={})

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
    badge_status = DEPENDENCY_STATUS_TO_BADGE_STATUS[max_level]
    result_dict['status'] = badge_status
    result_dict['details'] = outdated_depencdency_name_to_details
    result_dict['deprecated_deps'] = deprecated_deps

    return result_dict


def _get_badge_status(
        self_compat_res: dict,
        google_compat_res: dict,
        dependency_res: dict) -> BadgeStatus:
    """Get the badge status.

    The badge status will determine the right hand text and the color of
    the badge.

    Args:
        self_compat_res: a dict containing a package's self compatibility
            status for py2 and py3. See _get_self_compatibility_dict().
        google_compat_res: a dict containing a package's pair compatibility
            status for py2 and py3. See _get_pair_compatibility_dict().
        dependency_res: a dict containing a package's dependency status.
            See _get_dependency_dict().

    Returns:
        The cumulative badge status.
    """
    statuses = []
    for pyver in ['py2', 'py3']:
        statuses.append(self_compat_res[pyver]['status'])
        statuses.append(google_compat_res[pyver]['status'])
    statuses.append(dependency_res['status'])
    return BadgeStatus.get_highest_status(statuses)


def _badge_status_to_text(status: BadgeStatus) -> str:
    # TODO: Include the "(updating...)" or "(old") suffix if the results
    # are old.
    return status.value


def _get_check_results(package_name: str, commit_number: str = None):
    """Gets the compatibility and dependency check results.

    Returns a 3 tuple: self compatibility, pair compatibility, dependency dicts
    that are used to generate badge images and badge target pages.
    """
    default_status = BadgeStatus.UNKNOWN_PACKAGE
    self_compat_res = badge_utils._build_default_result(
        status=default_status, details={})
    google_compat_res = badge_utils._build_default_result(
        status=default_status, details={})
    dependency_res = badge_utils._build_default_result(
        status=default_status, include_pyversion=False, details={})

    # If a package is not whitelisted, return defaults
    if not compat_utils._is_package_in_whitelist([package_name]):
        return (self_compat_res, google_compat_res, dependency_res)

    try:
        self_compat_res = _get_self_compatibility_dict(package_name)
        google_compat_res = _get_pair_compatibility_dict(package_name)
        dependency_res = _get_dependency_dict(package_name)
    except Exception:
        logging.exception(
            'Exception checking results for "{}"'.format(package_name))
        error_status = BadgeStatus.INTERNAL_ERROR
        self_compat_res, google_compat_res, dependency_res = (
            badge_utils._build_default_result(status=error_status),
            badge_utils._build_default_result(status=error_status),
            badge_utils._build_default_result(
                status=error_status, include_pyversion=False))

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
        return 'compatibility check (PyPI)'


@app.route('/one_badge_image')
def one_badge_image():
    """Generate a badge that captures all checks."""
    package_name = flask.request.args.get('package')
    badge_name = flask.request.args.get('badge')

    commit_number = badge_utils._calculate_commit_number(package_name)
    self, google, dependency = _get_check_results(package_name)
    status = _get_badge_status(self, google, dependency)
    color = BADGE_STATUS_TO_COLOR[status]
    badge_name = _format_badge_name(package_name, badge_name, commit_number)
    details_link = '{}{}'.format(
        flask.request.url_root[:-1],
        flask.url_for('one_badge_target', package=package_name))

    badge_args = dict(
        left_text=badge_name,
        right_text=_badge_status_to_text(status),
        right_color=color,
        whole_link=details_link)

    if flask.current_app.config['TESTING']:
        response = flask.json.jsonify(**badge_args)
    else:
        badge = pybadges.badge(**badge_args)
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
