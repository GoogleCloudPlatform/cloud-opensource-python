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
"""A HTTP server that wraps pip_checker.

Requires Python 3.6 or later.

Example usage:

$ python3 compatibility_checker_server.py
$ curl "http://127.0.0.1:8888/?python-version=3&package=compatibility-lib" \
    | python3 -m json.tool
{
    "result": "SUCCESS",
    "packages": [
        "compatibility-lib"
    ],
    "description": null,
    "dependency_info": {
        "compatibility-lib": {
            "installed_version": "0.0.18",
            "installed_version_time": "2019-01-16T18:35:09",
            "latest_version": "0.0.18",
            "current_time": "2019-01-18T21:09:15.172255",
            "latest_version_time": "2019-01-16T18:35:09",
            "is_latest": true
        },
        "pip": {
            "installed_version": "18.1",
            "installed_version_time": "2018-10-05T11:20:31",
            "latest_version": "18.1",
            "current_time": "2019-01-18T21:09:15.166074",
            "latest_version_time": "2018-10-05T11:20:31",
            "is_latest": true
        },
        "setuptools": {
            "installed_version": "40.6.3",
            "installed_version_time": "2018-12-11T19:51:02",
            "latest_version": "40.6.3",
            "current_time": "2019-01-18T21:09:15.187775",
            "latest_version_time": "2018-12-11T19:51:02",
            "is_latest": true
        },
        "wheel": {
            "installed_version": "0.32.3",
            "installed_version_time": "2018-11-19T00:25:58",
            "latest_version": "0.32.3",
            "current_time": "2019-01-18T21:09:15.170863",
            "latest_version_time": "2018-11-19T00:25:58",
            "is_latest": true
        }
    }
}

For complete usage information:
$ python3 compatibility_checker_server.py --help

For production uses, this module exports a WSGI application called `app`.
For example:

$ gunicorn -w 4 --timeout 120 compatibility_checker_server:app

"""

import argparse
import configs
import flask
import logging
import os
import pprint
import sys
import wsgiref.simple_server

import pip_checker
import views

from google import auth as google_auth
from opencensus.stats import stats as stats_module
from opencensus.stats.exporters import stackdriver_exporter

PYTHON_VERSION_TO_COMMAND = {
    '2': ['python2', '-m', 'pip'],
    '3': ['python3', '-m', 'pip'],
}

STATS = stats_module.Stats()
app = flask.Flask(__name__)


def _get_project_id():
    # get project id from default setting
    try:
        _, project_id = google_auth.default()
    except google_auth.exceptions.DefaultCredentialsError:
        raise ValueError("Couldn't find Google Cloud credentials, set the "
                         "project ID with 'gcloud set project'")
    return project_id


def _enable_exporter():
    """Create and register the stackdriver exporter.

    For any data to be exported to stackdriver, an exporter needs to be created
    and registered with the view manager. Collected data will be reported via
    all the registered exporters. By not creating and registering an exporter,
    all collected data will stay local and will not appear on stackdriver.
    """
    project_id = _get_project_id()
    exporter = stackdriver_exporter.new_stats_exporter(
        stackdriver_exporter.Options(project_id=project_id))
    STATS.view_manager.register_exporter(exporter)


def _sanitize_packages(packages):
    """Checks if packages are whitelisted

    Args:
        packages: a list of packages
    Returns:
        a subset of packages that are whitelisted
    """
    sanitized_packages = []
    for pkg in packages:
        if pkg in configs.WHITELIST_PKGS or pkg in configs.WHITELIST_URLS:
            sanitized_packages.append(pkg)
    return sanitized_packages


@app.route('/health_check')
def health_check():
    return 'hello world'


@app.route('/')
def check():
    packages = flask.request.args.getlist('package')
    if not packages:
        return flask.make_response(
            "Request must specify at least one 'package' parameter", 400)

    sanitized_packages = _sanitize_packages(packages)
    unsupported_packages = frozenset(packages) - frozenset(sanitized_packages)
    if unsupported_packages:
        return flask.make_response(
            'Request contains unrecognized packages: {}'.format(
                ', '.join(unsupported_packages)), 400)

    python_version = flask.request.args.get('python-version')
    if not python_version:
        return flask.make_response(
            "Request must specify 'python-version' parameter", 400)
    if python_version not in PYTHON_VERSION_TO_COMMAND:
        return flask.make_response(
            'Invalid Python version specified. Must be one of: {}'.format(
                ', '.join(PYTHON_VERSION_TO_COMMAND), 400))

    python_command = PYTHON_VERSION_TO_COMMAND[python_version]

    try:
        pip_result = pip_checker.check(python_command, packages, STATS)
    except pip_checker.PipCheckerError as pip_error:
        return flask.make_response(pip_error.error_msg, 500)

    return flask.jsonify(
        result=pip_result.result_type.name,
        packages=pip_result.packages,
        description=pip_result.result_text,
        dependency_info=pip_result.dependency_info)


def main():

    class Handler(wsgiref.simple_server.WSGIRequestHandler):

        def log_message(self, format, *args):
            # Override the default log_message method to avoid logging
            # remote addresses.
            sys.stderr.write(
                "[%s] %s\n" % (self.log_date_time_string(), format % args))

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='host name to which the server should bind')
    parser.add_argument(
        '--port',
        type=int,
        default=8888,
        help='port to which the server should bind')
    export_metrics = os.environ.get('EXPORT_METRICS') is not None

    args = parser.parse_args()
    argsdict = vars(args)
    argsdict['export_metrics'] = export_metrics
    logging.info('Running server with:\n%s', pprint.pformat(argsdict))

    if export_metrics:
        _enable_exporter()

    # The views need to be registered with the view manager for data to be
    # collected. Once a view is registered, it reports data to any registered
    # exporters.
    for view in views.ALL_VIEWS:
        STATS.view_manager.register_view(view)

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)-8s %(asctime)s ' +
        '%(filename)s:%(lineno)s] %(message)s')

    with wsgiref.simple_server.make_server(
            args.host, args.port, app, handler_class=Handler) as httpd:
        httpd.serve_forever()


if __name__ == '__main__':
    main()
