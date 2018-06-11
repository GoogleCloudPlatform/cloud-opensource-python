"""Tests for pip_checker.

Uses a script "fake_pip.py" to simulate the behavior of the pip
(https://pypi.org/project/pip/) installation tool.
"""

import os.path
import unittest

import pip_checker


class TestPipChecker(unittest.TestCase):

    def setUp(self):
        self._fake_pip_path = os.path.join(os.path.dirname(__file__),
                                           'fake_pip.py')

    def test_success(self):
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--expected-install-args=-U,six',
                '--freeze-output=six==1.2.3\n'
            ],
            packages=['six'])
        self.assertEqual(
            check_result,
            pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.SUCCESS,
                result_text=None,
                requirements='six==1.2.3\n'))

    def test_success_with_clean(self):
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--expected-install-args=-U,six',
                '--uninstall-returncode=0', '--freeze-output=six==1.2.3\n'
            ],
            packages=['six'],
            clean=True)
        self.assertEqual(
            check_result,
            pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.SUCCESS,
                result_text=None,
                requirements='six==1.2.3\n'))

    def test_install_failure(self):
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--expected-install-args=-U,six',
                '--install-returncode=1', '--install-output=bad-install'
            ],
            packages=['six'])
        self.assertEqual(
            check_result,
            pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.INSTALL_ERROR,
                result_text='bad-install',
                requirements=None))

    def test_check_warning(self):
        check_result = pip_checker.check(
            pip_command=[
                self._fake_pip_path, '--check-returncode=1',
                '--check-output=bad-check', '--freeze-output=six==1.2.3\n'
            ],
            packages=['six'])
        self.assertEqual(
            check_result,
            pip_checker.PipCheckResult(
                packages=['six'],
                result_type=pip_checker.PipCheckResultType.CHECK_WARNING,
                result_text='bad-check',
                requirements='six==1.2.3\n'))

    def test_freeze_error(self):
        with self.assertRaises(pip_checker.PipError) as e:
            pip_checker.check(
                pip_command=[self._fake_pip_path, '--freeze-returncode=1'],
                packages=['six'])
        self.assertIn('freeze', e.exception.command)

    def test_uninstall_error(self):
        with self.assertRaises(pip_checker.PipError) as e:
            pip_checker.check(
                pip_command=[
                    self._fake_pip_path, '--expected-install-args=-U,six',
                    '--uninstall-returncode=1', '--freeze-output=six==1.2.3\n'
                ],
                packages=['six'],
                clean=True)
        self.assertIn('uninstall', e.exception.command)
