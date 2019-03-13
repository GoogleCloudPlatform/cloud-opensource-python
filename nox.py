# Copyright 2018 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Nox config for running lint and unit tests."""

from __future__ import absolute_import

import os

import nox

LOCAL_DEPS = ['compatibility_lib']


@nox.session
def lint(session):
    """Run yapf and return an error if yapf formatting is not used."""
    session.interpreter = 'python3.6'
    session.install('yapf')
    session.run('yapf', '--diff', '-r', '.',
                '--exclude=__pycache__,venv,dist,.git,build,.tox,.nox,.idea,'
                'mock_*,test_*,*_test')


@nox.session
@nox.parametrize('py', ['3.5', '3.6'])
def unit(session, py):
    """Run the unit test suite.

    Unit test files should be named like test_*.py and in the same directory
    as the file being tested.
    """
    session.interpreter = 'python{}'.format(py)

    # Install all test dependencies, then install this package in-place.
    session.install('-e', ','.join(LOCAL_DEPS))
    session.install('-r', 'requirements-test.txt')

    # Run py.test against the unit tests.
    session.run(
        'py.test',
        '--quiet',
        '.',
        '--ignore=system_test',
        *session.posargs
    )


@nox.session
@nox.parametrize('py', ['3.6'])
def system(session, py):
    """Run the system test suite."""

    # Sanity check: Only run system tests if the environment variable is set.
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip('Credentials must be set via environment variable.')

    # Run the system tests against latest Python 2 and Python 3 only.
    session.interpreter = 'python{}'.format(py)

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'sys-' + py

    # Build and install compatibility_lib
    session.install('-e', ','.join(LOCAL_DEPS))

    # Install all test dependencies.
    session.install('-r', 'requirements-test.txt')

    # Run py.test against the system tests.
    session.run(
        'py.test',
        '-s',
        'system_test/',
        # Skip the system test for compatibility server as circle ci does not
        # support running docker in docker.
        '--ignore=system_test/test_compatibility_checker_server.py',
        *session.posargs
    )


@nox.session
def update_dashboard(session):
    """Build the dashboard."""

    session.interpreter = 'python3.6'
    session.install('compatibility-lib')
    session.install('-r', 'requirements-test.txt')
    session.install('-e', ','.join(LOCAL_DEPS))

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'dashboard'

    session.chdir(os.path.realpath(os.path.dirname(__file__)))

    # Build the dashboard!
    session.run(
        'bash', os.path.join('.', 'scripts', 'update_dashboard.sh'))
