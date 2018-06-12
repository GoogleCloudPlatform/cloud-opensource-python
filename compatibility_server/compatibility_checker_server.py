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

# An image used to run a Python webserver that does compatibility checking
# between pip-installable packages.
#
# Contains three indenpendent versions of Python:
#  - python 3.6: used to run the web application
#  - python 3.6.5: used for python3 pip installation (build from source)
#  - python 2.7.15: used for python2 pip installation (build from source)

"""A HTTP server that wraps pip_checker."""

import argparse
import collections.abc
import json
import logging
import pprint
import threading
import urllib.parse
import wsgiref.simple_server

import pip_checker


def _parse_python_version_to_command_mapping(s):
    version_to_command = {}
    for version_mapping in s.split(','):
        try:
            version, command = version_mapping.split(':')
        except ValueError:
            raise argparse.ArgumentTypeError(
                ('{0} is not in the format of <version>:<command>,' +
                 '<version>:<command>').format(s))
        version_to_command[version] = command
    return version_to_command


class CompatibilityServer:

    def __init__(self, host, port, clean, python_version_to_command,
        install_once):
        self._host = host
        self._port = port
        self._clean = clean
        self._python_version_to_command = python_version_to_command
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

        if python_version not in self._python_version_to_command:
            start_response('400 Bad Request',
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return [
                b'Invalid Python version specified. Must be one of: %s' % (
                    ', '.join(
                        self._python_version_to_command).encode('utf-8'))
            ]
        python_command = self._python_version_to_command[python_version]

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
            requirements=pip_result.requirements)

        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(results).encode('utf-8')]

    def _wsgi_app(self, environ, start_response):
        # https://www.python.org/dev/peps/pep-0333/
        packages = []
        python_version = None

        if environ.get('REQUEST_METHOD') == 'GET':
            parameters = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
            packages = parameters.get('package', [])
            python_version = parameters.get('python-version', [None])[0]
        elif environ.get('REQUEST_METHOD') == 'POST':
            # TODO(bquinlan): Fix POST.
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            try:
                request = json.loads(environ['wsgi.input'].read(content_length))
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
        with wsgiref.simple_server.make_server(self._host, self._port,
                                               self._wsgi_app) as self._httpd:
            self._httpd.serve_forever()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format=
        '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] %(message)s')

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='host name to which the server should bind')
    parser.add_argument(
        '--port',
        type=int,
        default=8888,
        help=
        'port to which the server should bind')
    parser.add_argument(
        '--clean',
        action='store_true',
        help=
        'uninstall existing packages before performing dependency checking')
    parser.add_argument(
        '--install-once',
        action='store_true',
        help='exit after doing a single "pip install" command')
    parser.add_argument(
        '--python-versions',
        type=_parse_python_version_to_command_mapping,
        default='2:python2,3:python3',
        help=
        'maps version strings to the Python command to execute when running '
        'that version e.g. "2:python2;2,3:python3;3.5:/usr/bin/python3.5'
        ';3.6:/usr/bin/python3.6"')
    args = parser.parse_args()
    logging.info('Running server with:\n%s', pprint.pformat(vars(args)))
    CompatibilityServer(args.host, args.port, args.clean, args.python_versions,
                        args.install_once).serve()


if __name__ == '__main__':
    main()
