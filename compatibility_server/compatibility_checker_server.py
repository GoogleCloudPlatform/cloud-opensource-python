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
import json
import logging
import pprint
import sys
import threading
import typing
import urllib.parse
import wsgiref.simple_server

import pip_checker


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

    def __init__(self, host: str, port: int, clean: bool,
                 python_version_to_interpreter: typing.Mapping[str, str],
                 install_once: bool):
        """Initialize an HTTP server that checks for pip package compatibility.

        Args:
            host: The host name to listen on e.g. "localhost".
            port: The port number to listen on e.g. 80.
            clean: If True then uninstall previously installed packages before
                handling each request.
            python_version_to_interpreter: Maps python version e.g. "3" to
                a Python interpreter that can corresponds to that version e.g.
                "/usr/bin/python3.6"
            install_once: If True then the server will exit after handling a
                single request that involves installing pip packages.
        """
        self._host = host
        self._port = port
        self._clean = clean
        self._python_version_to_interpreter = python_version_to_interpreter
        self._install_once = install_once

    def _shutdown(self):
        threading.Thread(target=self._httpd.shutdown).start()

    def _check(self, start_response, python_version, packages):
        if not packages:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Request must specify at least one package']

        if not python_version:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Request must specify the Python version to use']

        if python_version not in self._python_version_to_interpreter:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [
                b'Invalid Python version specified. Must be one of: %s' % (
                    ', '.join(
                        self._python_version_to_interpreter).encode('utf-8'))
            ]
        python_command = self._python_version_to_interpreter[python_version]

        if self._install_once:
            self._shutdown()

        try:
            pip_result = pip_checker.check(
                [python_command, '-m', 'pip'], packages, clean=self._clean)
        except pip_checker.PipError as pip_error:
            start_response('500 Internal Server Error',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            with open(pip_error.stderr_path, 'r') as f:
                error_text = f.read()
            logging.error('pip command ("%s") failed with:\n%s\n',
                          pip_error.command_string, error_text)
            return [
                b'pip command ("%s") ' % pip_error.command_string.encode(
                    'utf-8'),
                b'failed with:\n',
                error_text.encode('utf-8'), b'\n'
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

        return self._check(start_response, python_version,
                           packages)

    def serve(self):
        class Handler(wsgiref.simple_server.WSGIRequestHandler):
            def log_message(self, format, *args):
                # Override the default log_message method to avoid logging
                # remote addresses.
                sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(),
                                                format % args))
        with wsgiref.simple_server.make_server(
                self._host, self._port,
                self._wsgi_app,
                handler_class=Handler) as self._httpd:
            self._httpd.serve_forever()


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
    parser.add_argument(
        '--clean',
        action='store_true',
        help='uninstall existing packages before performing dependency ' +
             'checking')
    parser.add_argument(
        '--install-once',
        action='store_true',
        help='exit after doing a single "pip install" command')
    parser.add_argument(
        '--python-versions',
        type=_parse_python_version_to_interpreter_mapping,
        default='2:python2,3:python3',
        help='maps version strings to the Python command to execute when ' +
             'running that version e.g. "2:python2;2,3:python3;' +
             '3.5:/usr/bin/python3.5;3.6:/usr/bin/python3.6"')
    args = parser.parse_args()
    logging.info('Running server with:\n%s', pprint.pformat(vars(args)))
    CompatibilityServer(args.host, args.port, args.clean, args.python_versions,
                        args.install_once).serve()


if __name__ == '__main__':
    main()
