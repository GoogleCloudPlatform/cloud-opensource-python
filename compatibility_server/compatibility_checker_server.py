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

$ python3 compatibility_checker_server.py \
     --host=0.0.0.0 --port=8888 \
     --python-version \
     2:python2,3:python3
$ curl 'http://0.0.0.0:8888/?package=six&python-version=3' \
    | python3 -m json.tool
{
    "result": "SUCCESS",
    "packages": [
        "six"
    ],
    "description": null,
    "requirements": "absl-py==0.2.2\napparmor==2.11.1\n..."
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
import pprint
import sys
import wsgiref.simple_server

import pip_checker

PYTHON_VERSION_TO_COMMAND = {
    '2': ['python2', '-m', 'pip'],
    '3': ['python3', '-m', 'pip'],
}


app = flask.Flask(__name__)


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
                ', '.join(unsupported_packages)),
            400)

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
        pip_result = pip_checker.check(
            python_command, packages)
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
            sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(),
                                            format % args))


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
    args = parser.parse_args()
    logging.info('Running server with:\n%s', pprint.pformat(vars(args)))

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)-8s %(asctime)s ' +
               '%(filename)s:%(lineno)s] %(message)s')

    with wsgiref.simple_server.make_server(
            args.host,
            args.port,
            app,
            handler_class=Handler) as httpd:
        httpd.serve_forever()



if __name__ == '__main__':
    main()
