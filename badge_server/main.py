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
import logging
import requests
import threading

import flask
import pybadges

import utils as badge_utils
from compatibility_lib import configs
from compatibility_lib import utils
from compatibility_lib import package as package_module


app = flask.Flask(__name__)

cache = badge_utils.initialize_cache()


def _get_result_from_cache(
        package_name: str,
        badge_type: badge_utils.BadgeType) -> dict:
    """Get check result from cache."""
    # Return unknown if package not in whitelist
    if not utils._is_package_in_whitelist([package_name]):
        result = badge_utils._build_default_result(
            badge_type=badge_type,
            status='UNKNOWN',
            details={})
    # Get the result from cache, return None if not in cache
    else:
        result = cache.get('{}_{}'.format(package_name, badge_type.value))

    if result is None:
        result = badge_utils._build_default_result(
            badge_type=badge_type,
            status='CALCULATING',
            details={})

    return result


def _get_pair_status_for_packages(pkg_sets):
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
    for pkg_set in pkg_sets:
        pkgs = [package_module.Package(pkg) for pkg in pkg_set]
        pair_res = badge_utils.store.get_pair_compatibility(pkgs)

        for res in pair_res:
            py_version = badge_utils.PY_VER_MAPPING[res.python_major_version]
            # Status showing one of the check failures
            if res.status.value != 'SUCCESS':
                # Ignore the package that not support for given py_ver
                if pkg_set[1] in \
                        configs.PKG_PY_VERSION_NOT_SUPPORTED.get(
                            res.python_major_version):
                    continue
                # Ignore the package that are not self compatible
                self_status = _get_result_from_cache(
                    package_name=pkg_set[1],
                    badge_type=badge_utils.BadgeType.SELF_COMP_BADGE)
                if self_status[py_version]['status'] != 'SUCCESS':
                    continue
                version_and_res[py_version]['status'] = res.status.value
                version_and_res[py_version]['details'][pkg_set[1]] = \
                    res.details if res.details is not None \
                        else badge_utils.EMPTY_DETAILS
    return version_and_res


def _get_all_results_from_cache(package_name):
    """Get all the check results from cache.
    
    Rules:
        - Return success status if all the check results are success.
        - Otherwise return warning status.
    """
    self_compat_res = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.SELF_COMP_BADGE)
    google_compat_res =_get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.GOOGLE_COMP_BADGE)
    dependency_res = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.DEP_BADGE)

    if self_compat_res['py3']['status'] == 'SUCCESS' and \
        google_compat_res['py3']['status'] == 'SUCCESS' and \
            dependency_res['status'] == 'UP_TO_DATE':
            status = 'SUCCESS'
    elif 'CALCULATING' in (
        self_compat_res['py3']['status'],
        google_compat_res['py3']['status'],
        dependency_res['status']
    ):
        status = 'CALCULATING'
    elif 'UNKNOWN' in (
        self_compat_res['py3']['status'],
        google_compat_res['py3']['status'],
        dependency_res['status']
    ):
        status = 'UNKNOWN'
    else:
        status = 'CHECK_WARNING'

    return status, self_compat_res, google_compat_res, dependency_res


@app.route('/')
def greetings():
    """This is for testing the server health."""
    return 'hello world'


@app.route('/one_badge_image')
def one_badge_image():
    """Generate the badge for all the checks."""
    package_name = flask.request.args.get('package')
    badge_name = flask.request.args.get('badge_name')

    if badge_name is None:
        badge_name = package_name

    badge_name = badge_utils._sanitize_badge_name(badge_name)

    force_run_check = flask.request.args.get('force_run_check')
    # Remove the last '/' from the url root
    url_prefix = flask.request.url_root[:-1]
    # Call the url for each badge to run the checks. This will populate the
    # individual caches, which are used to calculate the final image state.
    # Self compatibility badge
    requests.get(url_prefix + flask.url_for(
        'self_compatibility_badge_image',
        package=package_name,
        force_run_check=force_run_check))
    # Google compatibility badge
    requests.get(url_prefix + flask.url_for(
        'google_compatibility_badge_image',
        package=package_name,
        force_run_check=force_run_check))
    # Self dependency badge
    requests.get(url_prefix + flask.url_for(
        'self_dependency_badge_image',
        package=package_name,
        force_run_check=force_run_check))

    status, _, _, _ = _get_all_results_from_cache(package_name)
    color = badge_utils.STATUS_COLOR_MAPPING[status]

    details_link = url_prefix + flask.url_for('one_badge_target',
                                              package=package_name)

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
    status, self_compat_res, google_compat_res, dependency_res = \
        _get_all_results_from_cache(package_name)

    return flask.render_template(
        'one-badge.html',
        package_name=package_name,
        self_compat_res=self_compat_res,
        google_compat_res=google_compat_res,
        dependency_res=dependency_res)


@app.route('/self_compatibility_badge_image')
def self_compatibility_badge_image():
    """Badge showing whether a package is compatible with itself."""
    package_name = flask.request.args.get('package')
    force_run_check = flask.request.args.get('force_run_check')

    badge_name = flask.request.args.get('badge_name')

    if badge_name is None:
        badge_name = 'self compatibility'

    version_and_res = badge_utils._build_default_result(
        badge_type=badge_utils.BadgeType.SELF_COMP_BADGE,
        status='CALCULATING',
        details=None)

    def run_check():
        # First see if this package is already stored in BigQuery.
        package = package_module.Package(package_name)
        compatibility_status = badge_utils.store.get_self_compatibility(
            package)
        if compatibility_status:
            for res in compatibility_status:
                py_version = badge_utils.PY_VER_MAPPING[
                    res.python_major_version]
                version_and_res[py_version]['status'] = res.status.value
                version_and_res[py_version]['details'] = res.details \
                    if res.details is not None else badge_utils.EMPTY_DETAILS

        # If not pre stored in BigQuery, run the check for the package.
        else:
            py2_res = badge_utils.checker.check([package_name], '2')
            py3_res = badge_utils.checker.check([package_name], '3')

            version_and_res['py2']['status'] = py2_res.get('result')
            py2_description = py2_res.get('description')
            py2_details = badge_utils.EMPTY_DETAILS if py2_description \
                               is None else py2_description
            version_and_res['py2']['details'] = py2_details
            version_and_res['py3']['status'] = py3_res.get('result')
            py3_description = py3_res.get('description')
            py3_details = badge_utils.EMPTY_DETAILS if py3_description \
                               is None else py3_description
            version_and_res['py3']['details'] = py3_details

        # Write the result to Cloud Datastore
        cache.set(
            '{}_self_comp_badge'.format(package_name), version_and_res)

    if not utils._is_package_in_whitelist([package_name]):
        self_comp_res = badge_utils._build_default_result(
            badge_type=badge_utils.BadgeType.SELF_COMP_BADGE,
            status='UNKNOWN',
            details=badge_utils.PACKAGE_NOT_SUPPORTED)
    else:
        self_comp_res = cache.get('{}_self_comp_badge'.format(package_name))

    if self_comp_res is None:
        details = version_and_res
    else:
        details = self_comp_res

    # Run the check if details is None or forced to populate the cache.
    if self_comp_res is None or force_run_check is not None:
        threading.Thread(target=run_check).start()

    badge = badge_utils._get_badge(details, badge_name)
    response = flask.make_response(badge)
    response.content_type = badge_utils.SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/self_compatibility_badge_target')
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
    result_dict = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.SELF_COMP_BADGE)

    return flask.render_template(
        'self-compatibility.html',
        package_name=package_name,
        result=result_dict)


@app.route('/self_dependency_badge_image')
def self_dependency_badge_image():
    """Badge showing whether a package is has outdated dependencies."""

    package_name = flask.request.args.get('package')
    force_run_check = flask.request.args.get('force_run_check')
    badge_name = flask.request.args.get('badge_name')

    if badge_name is None:
        badge_name = 'dependency status'

    def run_check():
        res = {
            'status': 'UP_TO_DATE',
            'details': {},
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
            res['status'] = max_level.name
            res['details'] = details
            res['deprecated_deps'] = deprecated_deps

        # Write the result to Cloud Datastore
        cache.set(
            '{}_dependency_badge'.format(package_name), res)

    if not utils._is_package_in_whitelist([package_name]):
        dependency_res = badge_utils._build_default_result(
            badge_type=badge_utils.BadgeType.DEP_BADGE,
            status='UNKNOWN',
            details={})
    else:
        dependency_res = cache.get(
            '{}_dependency_badge'.format(package_name))

    if dependency_res is None:
        details = badge_utils.DEFAULT_DEPENDENCY_RESULT
    else:
        details = dependency_res

    # Run the check if dependency_res is None or forced to populate the cache.
    if dependency_res is None or force_run_check is not None:
        threading.Thread(target=run_check).start()

    badge = badge_utils._get_badge(details, badge_name)
    response = flask.make_response(badge)
    response.content_type = badge_utils.SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/self_dependency_badge_target')
def self_dependency_badge_target():
    """Return a dict that contains dependency status and details."""
    package_name = flask.request.args.get('package')
    result_dict = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.DEP_BADGE)

    return flask.render_template(
        'dependency-result.html',
        package_name=package_name,
        result=result_dict)


@app.route('/google_compatibility_badge_image')
def google_compatibility_badge_image():
    """Badge showing whether a package is compatible with Google OSS Python
    packages. If all packages success, status is SUCCESS; else set status
    to one of the failure types, details can be found at the target link."""
    package_name = flask.request.args.get('package')
    force_run_check = flask.request.args.get('force_run_check')
    badge_name = flask.request.args.get('badge_name')

    if badge_name is None:
        badge_name = 'google compatibility'

    def run_check():
        pkg_sets = [[package_name, pkg] for pkg in configs.PKG_LIST]
        if package_name in configs.PKG_LIST:
            result = _get_pair_status_for_packages(pkg_sets)
        else:
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

            for py_ver in [2, 3]:
                results = list(badge_utils.checker.get_pairwise_compatibility(
                    py_ver, pkg_sets))
                logging.warning(results)
                py_version = badge_utils.PY_VER_MAPPING[py_ver]

                for res in results:
                    res_item = res[0]
                    status = res_item.get('result')
                    package = res_item.get('packages')[1]
                    if status != 'SUCCESS':
                        # Ignore the package that not support for given py_ver
                        if package in \
                                configs.PKG_PY_VERSION_NOT_SUPPORTED.get(
                                py_ver):
                            continue

                        # Ignore the package that are not self compatible
                        self_status = _get_result_from_cache(
                            package_name=package_name,
                            badge_type=badge_utils.BadgeType.SELF_COMP_BADGE)
                        if self_status[py_version]['status'] not in [
                                'SUCCESS', 'CALCULATING']:
                            continue
                        # Status showing one of the check failures
                        version_and_res[
                            py_version]['status'] = res_item.get('result')
                        description = res_item.get('description')
                        details = badge_utils.EMPTY_DETAILS if description \
                                       is None else description
                        version_and_res[
                            py_version]['details'][package] = details
            result = version_and_res

        # Write the result to Cloud Datastore
        cache.set(
            '{}_google_comp_badge'.format(package_name), result)

    google_comp_res = cache.get(
        '{}_google_comp_badge'.format(package_name))

    if not utils._is_package_in_whitelist([package_name]):
        google_comp_res = badge_utils._build_default_result(
            badge_type=badge_utils.BadgeType.GOOGLE_COMP_BADGE,
            status='UNKNOWN',
            details={})

    if google_comp_res is None:
        details = badge_utils._build_default_result(
            badge_type=badge_utils.BadgeType.GOOGLE_COMP_BADGE,
            status='CALCULATING',
            details={})
    else:
        details = google_comp_res

    # Run the check if google_comp_res is None or forced to populate the cache.
    if google_comp_res is None or force_run_check is not None:
        threading.Thread(target=run_check).start()

    badge = badge_utils._get_badge(details, badge_name)
    response = flask.make_response(badge)
    response.content_type = badge_utils.SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/google_compatibility_badge_target')
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
    result_dict = _get_result_from_cache(
                      package_name=package_name,
                      badge_type=badge_utils.BadgeType.GOOGLE_COMP_BADGE)

    return flask.render_template(
        'google-compatibility.html',
        package_name=package_name,
        result=result_dict)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
