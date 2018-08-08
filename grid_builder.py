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
import tempfile
from typing import Iterable, Mapping
import webbrowser

import jinja2

from compatibility_lib import configs
from compatibility_lib import compatibility_store
from compatibility_lib import package

_JINJA2_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader('.'), autoescape=jinja2.select_autoescape())

_DEFAULT_INSTALL_NAMES = configs.PKG_LIST


class _ResultHolder():
    def __init__(self, package_to_results, pairwise_to_results):
        self._package_to_results = package_to_results
        self._pairwise_to_results = pairwise_to_results

    def _is_py_version_incompatible(self, result):
        if result.status == compatibility_store.Status.INSTALL_ERROR:
            for version in [2, 3]:
                for pkg in result.packages:
                    major_version = result.python_major_version
                    name = pkg.install_name
                    unsupported = configs.PKG_PY_VERSION_NOT_SUPPORTED[version]

                    if major_version == version and name in unsupported:
                        return True
        return False


    def get_result(self,
                   package_1: package.Package,
                   package_2: package.Package) -> Mapping[str, str]:
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
        if (not self._package_to_results[package_1] or
            not self._package_to_results[package_2]):
            return {
                'status': compatibility_store.Status.UNKNOWN.name,
                'self': True,
            }

        package_results = (
                self._package_to_results[package_1] +
                self._package_to_results[package_2])

        for pr in package_results:
            if not self._is_py_version_incompatible(pr) and \
                            pr.status != compatibility_store.Status.SUCCESS:
                return {
                    'status': pr.status.value,
                    'self': True,
                    'details': pr.details
                }

        if package_1 == package_2:
            return {
                'status': compatibility_store.Status.SUCCESS.name,
                'self': True,
            }
        else:
            pairwise_results = self._pairwise_to_results[
                frozenset([package_1, package_2])]
            if not pairwise_results:
                return {
                    'status': compatibility_store.Status.UNKNOWN.name,
                    'self': False,
                }
            for pr in pairwise_results:
                if not self._is_py_version_incompatible(pr) and \
                            pr.status != compatibility_store.Status.SUCCESS:
                    return {
                        'status': pr.status.value,
                        'self': False,
                        'details': pr.details
                    }
            return {
                'status': compatibility_store.Status.SUCCESS.name,
                'self': False,
            }


class GridBuilder:
    """Build a web page that shows package compatibility as a grid."""

    def __init__(self, store: compatibility_store.CompatibilityStore):
        self._store = store

    def build_grid(self, packages: Iterable[package.Package]) -> str:
        """Returns a web page compatibility grid given a list of packages."""
        packages = list(packages)
        package_to_results = self._store.get_self_compatibilities(packages)
        pairwise_to_results = self._store.get_compatibility_combinations(
            packages)

        results = _ResultHolder(package_to_results, pairwise_to_results)
        current_timestamp = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        template = _JINJA2_ENVIRONMENT.get_template('grid-template.html')
        return template.render(
            packages=packages,
            results=results,
            current_timestamp=current_timestamp)


def main():
    parser = argparse.ArgumentParser(
        description='Display a grid show the dependency compatibility ' +
                    'between Python packages')
    parser.add_argument('--packages', nargs='+',
                        default=_DEFAULT_INSTALL_NAMES,
                        help='the packages to display compatibility ' +
                             'information for')
    parser.add_argument(
        '--browser',
        action='store_true',
        default=False,
        help='display the grid in a browser tab')

    args = parser.parse_args()

    store = compatibility_store.CompatibilityStore()
    grid_builder = GridBuilder(store)
    grid_html = grid_builder.build_grid(
        (package.Package(install_name) for install_name in args.packages))

    if args.browser:
        _, grid_path = tempfile.mkstemp(suffix='.html')
        with open(grid_path, 'wt') as f:
            f.write(grid_html)
        webbrowser.open_new_tab('file://' + grid_path)
    else:
        print(grid_html, end='')


if __name__ == '__main__':
    main()
