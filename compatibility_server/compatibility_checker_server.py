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
"""

import argparse
import collections.abc
import configs
import json
import logging
import pprint
import urllib.parse
import wsgiref.simple_server

import pip_checker

PYTHON_VERSION_TO_COMMAND = {
    '2': ['python2', '-m', 'pip'],
    '3': ['python3', '-m', 'pip'],
}


def _parse_python_version_to_interpreter_mapping(s):
    version_to_interpreter = {}
    for version_mapping in s.split(','):
        try:
            version, command = version_mapping.split(':')
        except ValueError:
            raise argparse.ArgumentTypeError(
                ('{0} is not in the format of <version>:<command>,' +
                 '<version>:<command>').format(s))
        version_to_interpreter[version] = command
    return version_to_interpreter


class CompatibilityServer:

    def __init__(self, host: str, port: int):
        """Initialize an HTTP server that checks for pip package compatibility.

        Args:
            host: The host name to listen on e.g. "localhost".
            port: The port number to listen on e.g. 80.
        """
        self._host = host
        self._port = port

    def _check(self, start_response, python_version, packages):
        if not packages:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Request must specify at least one package']

        sanitized_packages = _sanitize_packages(packages)

        if sanitized_packages != packages:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Request contains third party github head packages.']

        if not python_version:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Request must specify the Python version to use']

        if python_version not in PYTHON_VERSION_TO_COMMAND:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [
                b'Invalid Python version specified. Must be one of: %s' % (
                    ', '.join(
                        PYTHON_VERSION_TO_COMMAND).encode('utf-8'))
            ]
        python_command = PYTHON_VERSION_TO_COMMAND[python_version]

        try:
            pip_result = pip_checker.check(
                python_command, packages)
        except pip_checker.PipCheckerError as pip_error:
            start_response('500 Internal Server Error',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            logging.error('Command failed with:\n%s\n',
                          pip_error.error_msg)
            return [
                b'pip command failed with:\n',
                pip_error.error_msg, b'\n'
            ]
        results = dict(
            result=pip_result.result_type.name,
            packages=pip_result.packages,
            description=pip_result.result_text,
            dependency_info=pip_result.dependency_info)

        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(results).encode('utf-8')]

    def _wsgi_app(self, environ, start_response):
        if environ.get('REQUEST_METHOD') == 'GET':
            parameters = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
            packages = parameters.get('package', [])
            python_version = parameters.get('python-version', [None])[0]
        elif environ.get('REQUEST_METHOD') == 'POST':
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            try:
                request = json.loads(
                    environ['wsgi.input'].read(content_length))
            except json.JSONDecodeError as e:
                start_response('400 Bad Request',
                               [('Content-Type', 'text/plain; charset=utf-8')])
                return [b'Invalid JSON payload: ', str(e).encode('utf-8')]

            if not isinstance(request, collections.abc.Mapping):
                start_response('400 Bad Request',
                               [('Content-Type', 'text/plain; charset=utf-8')])
                return [b'Request must contain a JSON object.']

            packages = request.get('packages', [])
            python_version = request.get('python-version', None)
        else:
            start_response('405 Method Not Allowed',
                           [('Content-Type', 'text/plain; charset=utf-8'),
                            ('Allow', 'GET, POST')])
            return [
                b'Method %s not supported' %
                environ.get('REQUEST_METHOD').encode('utf-8')
            ]

        return self._check(start_response, python_version, packages)

    def serve(self):
        with wsgiref.simple_server.make_server(self._host, self._port,
                                               self._wsgi_app) as self._httpd:
            self._httpd.serve_forever()


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


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)-8s %(asctime)s ' +
               '%(filename)s:%(lineno)s] %(message)s')

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
    CompatibilityServer(args.host, args.port).serve()


if __name__ == '__main__':
    main()
