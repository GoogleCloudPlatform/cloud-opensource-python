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
"""Creates a web page that shows the compatibility between packages as a grid.

For example:

------------------------------------------------------------
             |  absl-py | apache_beam | grpcio | tensorflow |
------------------------------------------------------------
absl-py      |   Good   |             |        |            |
apache_beam  |   Bad    |     Bad     |        |            |
grpcio       |   Good   |     Bad     |  Good  |            |
tensorflow   |   Good   |     Bad     |  Good  |    Good    |
------------------------------------------------------------
"""

import argparse
import datetime
import logging
import os
import signal
from typing import Any, Iterable, List, FrozenSet, Mapping
import webbrowser

from pexpect import popen_spawn

import jinja2

from compatibility_lib import configs
from compatibility_lib import compatibility_checker
from compatibility_lib import compatibility_store
from compatibility_lib import dependency_highlighter
from compatibility_lib import deprecated_dep_finder
from compatibility_lib import package

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

_JINJA2_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader('.'), autoescape=jinja2.select_autoescape())

_DEFAULT_INSTALL_NAMES = configs.PKG_LIST

SELF_SUCCESS = {'status': 'SUCCESS', 'self': True}

INSTANCE_CONNECTION_NAME = 'python-compatibility-tools:us-central1:' \
                           'compatibility-data'
PORT = '3306'


class DashboardBuilderError(Exception):
    pass


class _ResultHolder(object):

    def __init__(self,
                 package_to_results: Mapping[package.Package, List[
                     compatibility_store.CompatibilityResult]],
                 pairwise_to_results: Mapping[FrozenSet[package.Package], List[
                     compatibility_store.CompatibilityResult]],
                 package_with_dependency_info=None,
                 checker=None,
                 store=None):
        self._package_to_results = package_to_results
        self._pairwise_to_results = pairwise_to_results
        self._package_with_dependency_info = package_with_dependency_info
        self.checker = checker
        self.store = store
        self.deprecated_deps = self.get_deprecated_deps()
        self.dependency_to_update = \
            self.get_dependencies_needed_to_update()

    def _is_py_version_incompatible(self, result):
        if result.status != compatibility_store.Status.SUCCESS:
            for version in [2, 3]:
                for pkg in result.packages:
                    major_version = result.python_major_version
                    name = pkg.install_name
                    unsupported = configs.PKG_PY_VERSION_NOT_SUPPORTED[version]

                    if major_version == version and name in unsupported:
                        return True
        return False

    def has_issues(self, p: package.Package) -> bool:
        """Returns true if the given package has any issues.

        Currently check for:
            1. Self compatibility
            2. Pairwise compatibility
        """
        # Get self result
        for package_2 in self._package_to_results.keys():
            p_and_package_2_result = self.get_result(p, package_2)
            # Don't report the package as having issues if it is purely the
            # result of a self-incompatibility of another package.
            package_2_self_conflict = False
            package_2_self_res = self.get_result(package_2, package_2)
            if SELF_SUCCESS not in package_2_self_res.get(
                    'self_compatibility_check'):
                package_2_self_conflict = True
            pair_res = p_and_package_2_result.get(
                'pairwise_compatibility_check')
            for result in pair_res:
                if not package_2_self_conflict and \
                                result['status'] != 'SUCCESS':
                    return True

        return False

    def get_deprecated_deps(self) -> Mapping[str, List]:
        """
        Returns if there are deprecated dependencies for a
        given package as well as the list of deprecated deps for a package.
        """
        finder = deprecated_dep_finder.DeprecatedDepFinder(
            py_version='3', checker=self.checker, store=self.store)
        deprecated_deps = list(finder.get_deprecated_deps())

        results = {}
        for item in deprecated_deps:
            (pkg_name, deps) = item[0]
            results[pkg_name] = deps

        return results

    def has_deprecated_deps(self, p: package.Package) -> bool:
        return bool(self.deprecated_deps[p.install_name])

    def get_dependencies_needed_to_update(self) -> Mapping[str, List]:
        """
        Returns a dict of package names together with the dependencies that
        they need to update.
        """
        highlighter = dependency_highlighter.DependencyHighlighter(
            py_version='3', checker=self.checker, store=self.store)

        result = highlighter.check_packages(
            packages=configs.PKG_LIST, max_workers=10)
        return result

    def needs_update(self, p: package.Package) -> bool:
        """Returns whether the dependencies for a given package needs to
        update."""
        return bool(self.dependency_to_update[p.install_name])

    def get_statistics(self, packages):
        """Get the total number of packages that has issues."""
        total_packages = len(configs.PKG_LIST)
        total_have_conflicts = 0
        total_have_deprecated_deps = 0
        total_needs_update = 0

        outdated_or_deprecated_pkgs = set()

        for pkg in packages:
            if self.has_issues(pkg):
                total_have_conflicts += 1
            if self.has_deprecated_deps(pkg):
                total_have_deprecated_deps += 1
                outdated_or_deprecated_pkgs.add(pkg)
            if self.needs_update(pkg):
                total_needs_update += 1
                outdated_or_deprecated_pkgs.add(pkg)

        total_success_deps = total_packages - len(outdated_or_deprecated_pkgs)

        return total_packages, total_have_conflicts,\
            total_have_deprecated_deps, total_needs_update,\
            total_success_deps

    def get_package_details(self, p: package.Package):
        """Return the dict of package check summary.

        {
            'self_conflict': True,
            'pairwise_conflict': ['package1', 'package2'],
            'latest_version': '0.1.0',
        }
        """
        # The package being checked will appear in the dep list, but for
        # apache-beam[gcp], the package in dep list will just be apache-beam.
        self_dep_name = p.install_name
        if '[' in p.install_name:
            self_dep_name = p.install_name.split('[')[0]

        latest_version = self._package_with_dependency_info[
            p.install_name][self_dep_name]['latest_version']
        pairwise_conflict = []

        # Initialize the values
        result = {
            'self_conflict': False,
            'pairwise_conflict': pairwise_conflict,
            'latest_version': latest_version,
        }

        for pair_pkg in configs.PKG_LIST:
            check_result = self.get_result(p, package.Package(pair_pkg))
            # Get self compatibility status
            if pair_pkg == p.install_name:
                result['self_conflict'] = True \
                    if check_result['status_type'] != 'self-success' else False
            # Get pairwise compatibility status
            else:
                if check_result['status_type'] != 'pairwise-success' \
                        and self.has_issues(p):
                    pairwise_conflict.append(pair_pkg)

        result['pairwise_conflict'] = pairwise_conflict

        return result

    def get_result(self, package_1: package.Package,
                   package_2: package.Package) -> Mapping[str, Any]:
        """Returns the installation result of two packages.

        Args:
            package_1: One of the two packages to check installation
                compatibility with.
            package_2: One of the two packages to check installation
                compatibility with.

        Returns:
            The results of installing the two packages together, as a dict:

            {
                'status': <a compatibility_store.Status.value e.g. "SUCCESS">
                'self': <a bool indication whether the result is due to an
                         issue from within a single given package>
                'details': <a str representing the reason for any failure.
                            May be None.>
            }
        """
        self_result = []
        pair_result = []
        status_type = 'self-success'

        if (not self._package_to_results[package_1] or
                not self._package_to_results[package_2]):
            self_result.append({
                'status': compatibility_store.Status.UNKNOWN.name,
                'self': True,
            })
            status_type = 'self-unknown'

        package_results = (self._package_to_results[package_1] +
                           self._package_to_results[package_2])

        for pr in package_results:
            if not self._is_py_version_incompatible(pr) and \
                            pr.status != compatibility_store.Status.SUCCESS:
                self_result.append({
                    'status': pr.status.value,
                    'self': True,
                    'details': pr.details
                })
                status_type = 'self-' + pr.status.value.lower()

        if package_1 == package_2:
            if not self_result:
                self_result.append({
                    'status':
                    compatibility_store.Status.SUCCESS.name,
                    'self':
                    True,
                })
        else:
            pairwise_results = self._pairwise_to_results[frozenset(
                [package_1, package_2])]
            if not pairwise_results:
                pair_result.append({
                    'status':
                    compatibility_store.Status.UNKNOWN.name,
                    'self':
                    False,
                })
                status_type = 'pairwise-unknown'
            for pr in pairwise_results:
                if not self._is_py_version_incompatible(pr) and \
                            pr.status != compatibility_store.Status.SUCCESS:
                    pair_result.append({
                        'status': pr.status.value,
                        'self': False,
                        'details': pr.details
                    })
                    status_type = 'pairwise-' + pr.status.value.lower()

            if not pair_result:
                pair_result.append({
                    'status':
                    compatibility_store.Status.SUCCESS.name,
                    'self':
                    False,
                })
                if status_type == 'self-success':
                    status_type = 'pairwise-success'

        result = {
            'status_type': status_type,
            'self_compatibility_check': self_result,
            'pairwise_compatibility_check': pair_result
        }

        return result


class DashboardBuilder():
    """Build a web page that shows package compatibility status."""

    def __init__(self, packages: Iterable[package.Package],
                 results: _ResultHolder):
        self._packages = packages
        self._results = results

    def build_dashboard(self, template_name) -> str:
        """Returns a web page compatibility grid given a list of packages."""
        current_timestamp = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        template = _JINJA2_ENVIRONMENT.get_template(template_name)
        return template.render(
            packages=self._packages,
            results=self._results,
            current_timestamp=current_timestamp)


# TODO: Use helper function to reduce the length of main function.
def main():
    parser = argparse.ArgumentParser(
        description='Display a grid show the dependency compatibility ' +
        'between Python packages')
    parser.add_argument(
        '--packages',
        nargs='+',
        default=_DEFAULT_INSTALL_NAMES,
        help='the packages to display compatibility ' + 'information for')
    parser.add_argument(
        '--browser',
        action='store_true',
        default=False,
        help='display the grid in a browser tab')

    args = parser.parse_args()

    checker = compatibility_checker.CompatibilityChecker()
    store = compatibility_store.CompatibilityStore()

    instance_flag = '-instances={}=tcp:{}'.format(INSTANCE_CONNECTION_NAME,
                                                  PORT)
    cloud_sql_proxy_path = './cloud_sql_proxy'

    try:
        # Run cloud_sql_proxy
        process = popen_spawn.PopenSpawn([cloud_sql_proxy_path, instance_flag])
        process.expect('Ready for new connection', timeout=5)

        packages = [
            package.Package(install_name) for install_name in args.packages
        ]
        logging.info('Getting self compatibility results...')
        package_to_results = store.get_self_compatibilities(packages)
        logging.info('Getting pairwise compatibility results...')
        pairwise_to_results = store.get_compatibility_combinations(packages)

        package_with_dependency_info = {}
        for pkg in configs.PKG_LIST:
            dep_info = store.get_dependency_info(pkg)
            package_with_dependency_info[pkg] = dep_info

        results = _ResultHolder(package_to_results, pairwise_to_results,
                                package_with_dependency_info, checker, store)

        dashboard_builder = DashboardBuilder(packages, results)

        # Build the pairwise grid dashboard
        logging.info('Starting build the grid...')
        grid_html = dashboard_builder.build_dashboard(
            'dashboard/grid-template.html')
        grid_path = os.path.dirname(os.path.abspath(__file__)) + '/grid.html'
        with open(grid_path, 'wt') as f:
            f.write(grid_html)

        # Build the dashboard main page
        logging.info('Starting build the main dashboard...')
        main_html = dashboard_builder.build_dashboard(
            'dashboard/main-template.html')

        main_path = os.path.dirname(os.path.abspath(__file__)) + '/index.html'
        with open(main_path, 'wt') as f:
            f.write(main_html)
    except Exception:
        raise DashboardBuilderError('Error occurs when building dashboard.'
                                    'Output: {}'.format(process.before))
    finally:
        process.kill(signal.SIGTERM)

    if args.browser:
        webbrowser.open_new_tab('file://' + main_path)


if __name__ == '__main__':
    main()
