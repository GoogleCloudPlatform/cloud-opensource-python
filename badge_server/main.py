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
import os
import requests
import threading

import flask
import pybadges

from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import configs
from compatibility_lib import dependency_highlighter
from compatibility_lib import deprecated_dep_finder
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

if os.environ.get('RUN_LOCALLY') is not None:
    import fake_cache
    CACHE = fake_cache.FakeCache()
elif os.environ.get('REDISHOST') is not None:
    import redis_cache
    CACHE = redis_cache.RedisCache()
else:
    import datastore_cache
    CACHE = datastore_cache.DatastoreCache()

checker = compatibility_checker.CompatibilityChecker()
store = compatibility_store.CompatibilityStore()
highlighter = dependency_highlighter.DependencyHighlighter(
    checker=checker, store=store)
finder = deprecated_dep_finder.DeprecatedDepFinder(
    checker=checker, store=store)
priority_level = dependency_highlighter.PriorityLevel

URL_PREFIX = 'https://img.shields.io/badge/'

PY_VER_MAPPING = {
    2: 'py2',
    3: 'py3',
}

STATUS_COLOR_MAPPING = {
    'SUCCESS': 'green',
    'UNKNOWN': 'purple',
    'INSTALL_ERROR': 'yellow',
    'CHECK_WARNING': 'red',
    'CALCULATING': 'blue',
    'CONVERSION_ERROR': 'orange',
}

DEFAULT_COMPATIBILITY_RESULT = {
        'py2': {
            'status': 'CALCULATING',
            'details': {},
        },
        'py3': {
            'status': 'CALCULATING',
            'details': {},
        }
}

DEFAULT_DEPENDENCY_RESULT = {
        'status': 'CALCULATING',
        'details': {},
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

DEP_STATUS_COLOR_MAPPING = {
    'CALCULATING':                      'blue',
    'CONVERSION_ERROR':                 'purple',
    priority_level.UP_TO_DATE.name:     'green',
    priority_level.LOW_PRIORITY.name:   'yellow',
    priority_level.HIGH_PRIORITY.name:  'red'
}

DEP_CONVERSION_ERROR_RES = {
    'status': 'CONVERSION_ERROR',
    'details': None,
}

GITHUB_HEAD_NAME = 'github head'

SVG_CONTENT_TYPE = 'image/svg+xml'

EMPTY_DETAILS = 'NO DETAILS'

DEP_BADGE = 'dep_badge'
SELF_COMP_BADGE = 'self_comp_badge'
GOOGLE_COMP_BADGE = 'google_comp_badge'
API_BADGE = 'api_badge'

CACHED_PACKAGES = configs.PKG_LIST + configs.THIRD_PARTY_PACKAGE_LIST


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
                # Ignore the package that not support for given py_ver
                if pkg_set[1] in \
                        configs.PKG_PY_VERSION_NOT_SUPPORTED.get(
                            res.python_major_version):
                    continue
                # Ignore the package that are not self compatible
                self_status = _get_self_compatibility_from_cache(pkg_set[1])
                if self_status[py_version]['status'] not in [
                        'SUCCESS', 'CALCULATING']:
                    continue
                version_and_res[py_version]['status'] = res.status.value
                version_and_res[py_version]['details'][pkg_set[1]] = \
                    res.details if res.details is not None else EMPTY_DETAILS
    return version_and_res


def _sanitize_badge_name(badge_name):
    # If the package is from github head, replace the github url to
    # 'github head'
    if 'github.com' in badge_name:
        badge_name = GITHUB_HEAD_NAME

    return badge_name


def _get_badge(res, badge_name):
    badge_name = _sanitize_badge_name(badge_name)
    status = res.get('status')
    if status is not None:
        color = DEP_STATUS_COLOR_MAPPING[status]
    else:
        status = res['py3']['status']
        if status == 'SUCCESS' and \
            badge_name not in \
                configs.PKG_PY_VERSION_NOT_SUPPORTED.get(2):
            status = res['py2']['status']

        color = STATUS_COLOR_MAPPING[status]

    status = status.replace('_', ' ')
    return pybadges.badge(
        left_text=badge_name,
        right_text=status,
        right_color=color)


def _get_self_compatibility_from_cache(package_name):
    result_dict = CACHE.get(
        '{}_self_comp_badge'.format(package_name))

    if result_dict is None:
        result_dict = DEFAULT_COMPATIBILITY_RESULT
    return result_dict


def _get_google_compatibility_from_cache(package_name):
    result_dict = CACHE.get(
        '{}_google_comp_badge'.format(package_name))

    if result_dict is None:
        result_dict = DEFAULT_COMPATIBILITY_RESULT

    return result_dict


def _get_dependency_result_from_cache(package_name):
    result_dict = CACHE.get(
        '{}_dependency_badge'.format(package_name))

    if result_dict is None:
        result_dict = DEFAULT_DEPENDENCY_RESULT

    return result_dict


def _get_all_results_from_cache(package_name):
    self_compat_res = _get_self_compatibility_from_cache(package_name)
    google_compat_res = _get_google_compatibility_from_cache(package_name)
    dependency_res = _get_dependency_result_from_cache(package_name)

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
    else:
        status = 'CHECK_WARNING'

    return status, self_compat_res, google_compat_res, dependency_res


@app.route('/')
def greetings():
    return 'hello world'


@app.route('/one_badge_image')
def one_badge_image():
    package_name = flask.request.args.get('package')
    badge_name = flask.request.args.get('badge_name')

    if badge_name is None:
        badge_name = package_name

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
    color = STATUS_COLOR_MAPPING[status]

    details_link = url_prefix + flask.url_for('one_badge_target',
                                              package=package_name)
    response = flask.make_response(
        pybadges.badge(
            left_text=badge_name,
            right_text=status,
            right_color=color,
            whole_link=details_link))
    response.content_type = SVG_CONTENT_TYPE
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

        # Write the result to Cloud Datastore
        CACHE.set(
            '{}_self_comp_badge'.format(package_name), version_and_res)

    self_comp_res = CACHE.get(
        '{}_self_comp_badge'.format(package_name))

    if self_comp_res is None:
        details = version_and_res
    else:
        details = self_comp_res

    # Run the check if there is not cached result or forced to populate the
    # cache or package not in cached package list.
    if self_comp_res is None or \
        force_run_check is not None or \
            package_name not in CACHED_PACKAGES:
        threading.Thread(target=run_check).start()

    badge = _get_badge(details, badge_name)
    response = flask.make_response(badge)
    response.content_type = SVG_CONTENT_TYPE
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
    result_dict = _get_self_compatibility_from_cache(package_name)

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
            'status': 'CALCULATING',
            'details': {},
        }
        outdated = highlighter.check_package(package_name)
        deprecated_deps_list = finder.get_deprecated_dep(package_name)[1]
        deprecated_deps = ', '.join(deprecated_deps_list)
        details = {}

        max_level = priority_level.UP_TO_DATE
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
        CACHE.set(
            '{}_dependency_badge'.format(package_name), res)

    dependency_res = CACHE.get(
        '{}_dependency_badge'.format(package_name))

    if dependency_res is None:
        details = DEFAULT_DEPENDENCY_RESULT
    else:
        details = dependency_res

    # Run the check if there is not cached result or forced to populate the
    # cache or package not in cached package list.
    if dependency_res is None or \
        force_run_check is not None or \
            package_name not in CACHED_PACKAGES:
        threading.Thread(target=run_check).start()

    badge = _get_badge(details, badge_name)
    response = flask.make_response(badge)
    response.content_type = SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/self_dependency_badge_target')
def self_dependency_badge_target():
    """Return a dict that contains dependency status and details."""
    package_name = flask.request.args.get('package')
    result_dict = _get_dependency_result_from_cache(package_name)

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
                results = list(checker.get_pairwise_compatibility(
                    py_ver, pkg_sets))
                logging.warning(results)
                py_version = PY_VER_MAPPING[py_ver]

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
                        self_status = _get_self_compatibility_from_cache(
                            package)
                        if self_status[py_version]['status'] not in [
                                'SUCCESS', 'CALCULATING']:
                            continue
                        # Status showing one of the check failures
                        version_and_res[
                            py_version]['status'] = res_item.get('result')
                        description = res_item.get('description')
                        details = EMPTY_DETAILS if description is None \
                            else description
                        version_and_res[
                            py_version]['details'][package] = details
            result = version_and_res

        # Write the result to Cloud Datastore
        CACHE.set(
            '{}_google_comp_badge'.format(package_name), result)

    google_comp_res = CACHE.get(
        '{}_google_comp_badge'.format(package_name))

    if google_comp_res is None:
        details = DEFAULT_COMPATIBILITY_RESULT
    else:
        details = google_comp_res

    # Run the check if there is not cached result or forced to populate the
    # cache or package not in cached package list.
    if google_comp_res is None or \
        force_run_check is not None or \
            package_name not in CACHED_PACKAGES:
        threading.Thread(target=run_check).start()

    badge = _get_badge(details, badge_name)
    response = flask.make_response(badge)
    response.content_type = SVG_CONTENT_TYPE
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
    result_dict = _get_google_compatibility_from_cache(package_name)

    return flask.render_template(
        'google-compatibility.html',
        package_name=package_name,
        result=result_dict)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
