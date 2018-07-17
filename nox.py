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
        '--cov={}'.format('compatibility_lib'),
        '--cov-append',
        '--cov-config=.coveragerc',
        '--cov-report=',
        '--cov-fail-under=97',
        *LINT_UNIT_DIR,
        *session.posargs
    )


@nox.session
def cover(session):
    """Run the final coverage report.
    This outputs the coverage report aggregating coverage from the unit
    test runs (not system test runs), and then erases coverage data.
    """
    session.interpreter = 'python3.6'
    session.install('coverage', 'pytest-cov')
    session.run('coverage', 'report', '--show-missing', '--fail-under=100')
    session.run('coverage', 'erase')


# @nox.session
# def update_dashboard(session):
#     """Build the dashboard."""
#
#     session.interpreter = 'python3.6'
#     session.install('-e', ','.join(LOCAL_DEPS))
#     session.install('-r', 'requirements-test.txt')
#
#     # Set the virtualenv dirname.
#     session.virtualenv_dirname = 'dashboard'
#
#     session.chdir(os.path.realpath(os.path.dirname(__file__)))
#
#     # Build the dashboard!
#     session.run(
#         'bash', os.path.join('.', 'scripts', 'update_dashboard.sh'))
