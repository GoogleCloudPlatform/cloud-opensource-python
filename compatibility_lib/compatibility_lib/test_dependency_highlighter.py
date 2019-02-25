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

import json
import mock
import unittest

from datetime import timedelta
from compatibility_lib import dependency_highlighter
from compatibility_lib import utils
from compatibility_lib.testdata import mock_depinfo_data


def _get_dep_info(datetime=True):
    dep_info = json.loads(mock_depinfo_data.DEP_INFO)
    if not datetime:
        return dep_info

    fields = (
        'installed_version_time',
        'latest_version_time',
        'current_time')
    for _, info in dep_info.items():
        for field in fields:
            time = info[field]
            info[field] = utils._parse_datetime(time)
    return dep_info


class TestPriority(unittest.TestCase):

  def test_constructor_default(self):
        expected_level = dependency_highlighter.PriorityLevel.UP_TO_DATE
        expected_details = ''

        priority = dependency_highlighter.Priority()

        self.assertEqual(expected_level, priority.level)
        self.assertEqual(expected_details, priority.details)

  def test_constructor_explicit(self):
        expected_level = dependency_highlighter.PriorityLevel.LOW_PRIORITY
        expected_details = 'this is a test'

        priority = dependency_highlighter.Priority(
            level=expected_level,
            details=expected_details)

        self.assertEqual(expected_level, priority.level)
        self.assertEqual(expected_details, priority.details)


class TestOutdatedDependency(unittest.TestCase):
    expected_pkgname = 'google-cloud-bigquery'
    expected_parent = 'apache-beam[gcp]'
    expected_priority = dependency_highlighter.Priority(
        dependency_highlighter.PriorityLevel.HIGH_PRIORITY,
        'this dependency is 1 or more major versions behind the latest')
    expected_info = _get_dep_info()[expected_pkgname]

    expected_repr = (
        "OutdatedDependency<'google-cloud-bigquery', "
        "HIGH_PRIORITY>")

    expected_str = (
        'Dependency Name:\tgoogle-cloud-bigquery\n'
        'Priority:\t\tHIGH_PRIORITY\n'
        'Installed Version:\t0.25.0\n'
        'Latest Available:\t1.5.0\n'
        'Time Since Latest:\t14 days\n'
        'this dependency is 1 or more major versions '
        'behind the latest\n')

    outdated = dependency_highlighter.OutdatedDependency(
        pkgname=expected_pkgname,
        parent=expected_parent,
        priority=expected_priority,
        info=expected_info)

    def test_constructor(self):
        self.assertEqual(self.expected_pkgname, self.outdated.name)
        self.assertEqual(self.expected_parent, self.outdated.parent)
        self.assertEqual(self.expected_priority, self.outdated.priority)
        self.assertEqual(
            self.expected_info['installed_version'],
            self.outdated.installed_version)
        self.assertEqual(
            self.expected_info['installed_version_time'],
            self.outdated.installed_version_time)
        self.assertEqual(
            self.expected_info['latest_version'],
            self.outdated.latest_version)
        self.assertEqual(
            self.expected_info['latest_version_time'],
            self.outdated.latest_version_time)
        self.assertEqual(
            self.expected_info['current_time'],
            self.outdated.current_time)

    def test_repr(self):
        self.assertEqual(self.expected_repr, self.outdated.__repr__())

    def test_str(self):
        self.assertEqual(self.expected_str, str(self.outdated))


class TestDependencyHighlighter(unittest.TestCase):

    def setUp(self):
        self.expected_dep_info = _get_dep_info()
        self.expected_check_package_res = (
            "OutdatedDependency<'apache-beam', LOW_PRIORITY>",
            "OutdatedDependency<'dill', LOW_PRIORITY>",
            "OutdatedDependency<'google-apitools', LOW_PRIORITY>",
            "OutdatedDependency<'google-cloud-bigquery', HIGH_PRIORITY>",
            "OutdatedDependency<'google-cloud-core', HIGH_PRIORITY>",
            "OutdatedDependency<'google-cloud-pubsub', HIGH_PRIORITY>",
            "OutdatedDependency<'google-gax', LOW_PRIORITY>",
            "OutdatedDependency<'httplib2', LOW_PRIORITY>",
            "OutdatedDependency<'ply', HIGH_PRIORITY>")

        self._store = mock.Mock()
        self._store.get_dependency_info.return_value = _get_dep_info()

        fake_value = [[{'dependency_info': _get_dep_info(False)}]]
        self._checker = mock.Mock()
        self._checker.get_compatibility.return_value = fake_value

    def setup_test__get_update_priority(self):
        low = dependency_highlighter.PriorityLevel.LOW_PRIORITY
        high = dependency_highlighter.PriorityLevel.HIGH_PRIORITY

        not_updated = 'PACKAGE is not up to date with the latest version'

        six_months = ('it has been over 6 months since the latest version '
                      'for PACKAGE was released')

        three_minor = ('PACKAGE is 3 or more minor versions '
                       'behind the latest version')

        thirty_days = ('it has been over 30 days since the major version '
                       'for PACKAGE was released')

        major_version = ('PACKAGE is 1 or more major versions '
                         'behind the latest version')

        highlighter = dependency_highlighter.DependencyHighlighter(
            checker=self._checker, store=self._store)

        def dictify(args):
            major, minor, patch = args
            return {'major': major, 'minor': minor, 'patch': patch}

        def expect(level, msg):
            return dependency_highlighter.Priority(level, msg)

        def run(install_tup, latest_tup, numdays):
            install, latest = dictify(install_tup), dictify(latest_tup)
            res = highlighter._get_update_priority(
                'PACKAGE', install, latest, timedelta(days=numdays))
            return res

        cases = [
            (expect(low, not_updated),    run((2,5,0), (2,6,0), 5)),
            (expect(high, six_months),    run((2,5,0), (2,6,0), 200)),
            (expect(high, three_minor),   run((2,5,0), (2,8,0), 13)),
            (expect(low, not_updated),    run((2,5,0), (3,0,0), 29)),
            (expect(high, thirty_days),   run((2,5,0), (3,0,0), 50)),
            (expect(high, major_version), run((2,5,0), (3,0,4), 1)),
            (expect(high, major_version), run((2,5,0), (5,0,4), 1)),
        ]

        return cases

    def test__get_update_priority(self):
        def comp(p1, p2):
            if p1.level != p2.level:
                return False
            if p1.details != p2.details:
                return False
            return True

        cases = self.setup_test__get_update_priority()

        for expected, res in cases:
            self.assertTrue(comp(expected, res))

    def test_check_package(self):
        highlighter = dependency_highlighter.DependencyHighlighter(
            checker=self._checker, store=self._store)
        res = highlighter.check_package('apache-beam[gcp]')

        reprs = [repr(dep) for dep in res]
        reprs.sort()

        zipped = zip(self.expected_check_package_res, reprs)
        for expected, got in zipped:
            self.assertEqual(expected, got)

        highlighter = dependency_highlighter.DependencyHighlighter(
            checker=self._checker, store=self._store)
        res = highlighter.check_package('not-in-bigquery')

        reprs = [repr(dep) for dep in res]
        reprs.sort()

        zipped = zip(self.expected_check_package_res, reprs)
        for expected, got in zipped:
            self.assertEqual(expected, got)

    def test_check_packages(self):
        packages = ['apache-beam[gcp]', 'not-in-bigquery']
        highlighter = dependency_highlighter.DependencyHighlighter(
            checker=self._checker, store=self._store)
        res = highlighter.check_packages(packages)

        for pkgname, outdated in res.items():
            reprs = [repr(dep) for dep in outdated]
            reprs.sort()

            zipped = zip(self.expected_check_package_res, reprs)
            for expected, got in zipped:
                self.assertEqual(expected, got)


class TestUtilityFunctions(unittest.TestCase):
    good_tags = [
        ('1.1',         (1, 1, 0)),
        ('2018.5.90',   (2018, 5, 90)),
        ('10.1.0.1',    (10, 1, 0)),
    ]

    bad_tags = [
        '3', 'abc', '1.a2.0', '4..5.0', '6.30.1-dev',
        '2.2.2rc', '1.0.dev', '2.1a0', '1.1rc3'
    ]

    def test__sanitize_release_tag(self):
        for tag, expected in self.good_tags:
            major, minor, patch = expected
            release_info = dependency_highlighter._sanitize_release_tag(tag)
            self.assertEqual(release_info['major'], major)
            self.assertEqual(release_info['minor'], minor)
            self.assertEqual(release_info['patch'], patch)

        for tag in self.bad_tags:
            with self.assertRaises(dependency_highlighter.UnstableReleaseError):
                dependency_highlighter._sanitize_release_tag(tag)
