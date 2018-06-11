#!/usr/bin/env python3

"""A fake implementation of pip whose behavior can be modified using flags."""

import argparse
import sys


def assert_args(expected, actual):
    if expected and expected != actual:
        print('{!r} != {!r}'.format(expected, actual), end='', file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--install-returncode',
        type=int,
        default=0,
        help='the return code for "pip install"')
    parser.add_argument(
        '--install-output',
        default='install',
        help='the stderr output for "pip install"')

    parser.add_argument(
        '--check-returncode',
        type=int,
        default=0,
        help='the return code for "pip check"')
    parser.add_argument(
        '--check-output',
        default='check',
        help='the stdout output for "pip check"')

    parser.add_argument(
        '--freeze-returncode',
        type=int,
        default=0,
        help='the return code for "pip freeze"')
    parser.add_argument(
        '--freeze-output',
        default='freeze',
        help='the stdout output for "pip freeze"')

    parser.add_argument(
        '--uninstall-returncode',
        type=int,
        default=1,
        help='the return code for "pip uninstall"')

    parser.add_argument(
        '--expected-install-args',
        type=lambda s: s.split(','),
        default=[],
        help='the expected arguments for "pip install <arguments>"')

    known, unknown_args = parser.parse_known_args()
    command, *command_args = unknown_args

    if command == 'install':
        assert_args(known.expected_install_args, command_args)
        print(known.install_output, end='', file=sys.stderr)
        sys.exit(known.install_returncode)
    elif command == 'check':
        assert_args([], command_args)
        print(known.check_output, end='')
        sys.exit(known.check_returncode)
    elif command == 'freeze':
        assert_args([], command_args)
        print(known.freeze_output, end='')
        sys.exit(known.freeze_returncode)
    elif command == 'uninstall':
        sys.exit(known.uninstall_returncode)
    else:
        print('unexpected command: {}'.format(command), end='', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
