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


import flask
import pybadges

import utils as badge_utils
from compatibility_lib import utils


app = flask.Flask(__name__)

cache = badge_utils.initialize_cache()


def _get_result_from_cache(
        package_name: str,
        badge_type: badge_utils.BadgeType,
        commit_number: str = None) -> dict:
    """Get check result from cache."""
    # Return unknown if package not in whitelist
    if not utils._is_package_in_whitelist([package_name]):
        result = badge_utils._build_default_result(
            badge_type=badge_type,
            status='UNKNOWN',
            details={})
    # Get the result from cache, return None if not in cache
    else:
        package_key = '{}_{}'.format(
            package_name, commit_number) if commit_number else package_name
        result = cache.get('{}_{}'.format(package_key, badge_type.value))

    if result is None:
        result = badge_utils._build_default_result(
            badge_type=badge_type,
            status='CALCULATING',
            details={})

    return result


def _get_all_results_from_cache(package_name, commit_number=None):
    """Get all the check results from cache.

    Rules:
        - Return success status if all the check results are success.
        - Otherwise return warning status.
    """
    self_compat_res = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.SELF_COMP_BADGE,
        commit_number=commit_number)
    google_compat_res = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.GOOGLE_COMP_BADGE,
        commit_number=commit_number)
    dependency_res = _get_result_from_cache(
        package_name=package_name,
        badge_type=badge_utils.BadgeType.DEP_BADGE,
        commit_number=commit_number)

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

    commit_number = badge_utils._calculate_commit_number(package_name)
    status, timestamp, _, _, _ = _get_all_results_from_cache(
        package_name, commit_number=commit_number)
    color = badge_utils.STATUS_COLOR_MAPPING[status]

    # Include the check timestamp for github head
    if is_github and timestamp:
        badge_name = '{} {}'.format(badge_name, timestamp)

    response = flask.make_response(
        pybadges.badge(
            left_text=badge_name,
            right_text=status,
            right_color=color))
    response.content_type = badge_utils.SVG_CONTENT_TYPE
    response.headers['Cache-Control'] = 'no-cache'
    response.add_etag()

    return response


@app.route('/one_badge_target')
def one_badge_target():
    package_name = flask.request.args.get('package')
    commit_number = badge_utils._calculate_commit_number(package_name)

    status, _, self_compat_res, google_compat_res, dependency_res = \
        _get_all_results_from_cache(package_name, commit_number)

    return flask.render_template(
        'one-badge.html',
        package_name=package_name,
        self_compat_res=self_compat_res,
        google_compat_res=google_compat_res,
        dependency_res=dependency_res,
        commit_number=commit_number)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
