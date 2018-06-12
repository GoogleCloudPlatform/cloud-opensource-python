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

import nox

LINT_UNIT_DIR = ['compatibility_server',]


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
@nox.parametrize('py', ['3.6'])
def unit(session, py):
    """Run the unit test suite.
    
    Unit test files should be named like test_*.py and in the same directory
    as the file being tested.
    """

    # Run unit tests against all supported versions of Python.
    session.interpreter = 'python{}'.format(py)

    # Run py.test against the unit tests.
    session.run(
        'py.test',
        '--quiet',
        ','.join(LINT_UNIT_DIR),
        *session.posargs
    )
