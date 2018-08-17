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

LINT_UNIT_DIR = ['compatibility_server', '.']

LOCAL_DEPS = ['compatibility_lib']


@nox.session
def lint(session):
    """Run flake8.

    Returns a failure if flake8 finds linting errors or sufficiently
    serious code quality issues.
    """
    session.interpreter = 'python3.6'
    session.install('flake8')
    session.run('flake8',
                ','.join(LINT_UNIT_DIR),
                '--exclude=test_*')


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
        *LINT_UNIT_DIR,
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

    # Install all test dependencies.
    session.install('-r', 'requirements-test.txt')

    # Run py.test against the system tests.
    session.run(
        'py.test',
        '-s',
        'system_test/',
        *session.posargs
    )


@nox.session
def update_dashboard(session):
    """Build the dashboard."""

    session.interpreter = 'python3.6'
    session.install('-e', ','.join(LOCAL_DEPS))
    session.install('-r', 'requirements-test.txt')

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'dashboard'

    session.chdir(os.path.realpath(os.path.dirname(__file__)))

    # Build the dashboard!
    session.run(
        'bash', os.path.join('.', 'scripts', 'update_dashboard.sh'))
