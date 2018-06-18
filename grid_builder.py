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

"""

"""

import argparse
import itertools
import tempfile
from typing import Iterable
import webbrowser

import jinja2

from compatibility_lib import compatibility_store
from compatibility_lib import package


_JINJA2_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader('.'), autoescape=jinja2.select_autoescape())

_DEFAULT_INSTALL_NAMES = [
    'absl-py',
    'apache_beam',
    'google-cloud-bigtable',
    'grpcio',
    'pyclif',
    'pytype',
    'tensorflow',
]


class _ResultHolder():
    def __init__(self, package_to_results, pairwise_to_results):
        self._package_to_results = package_to_results
        self._pairwise_to_results = pairwise_to_results

    def get_result(self, install_name_1, install_name_2):
        """Returns the installation result of two packages.

        Args:
            install_name_1: The name of one package (as would be used in the
                "pip install" command e.g. "tensorflow" or
                "git+git://github.com/apache/beam#subdirectory=sdks/python").
            install_name_2: The name of one package (as would be used in the
                "pip install" command e.g. "tensorflow" or
                "git+git://github.com/apache/beam#subdirectory=sdks/python").

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
        install_names = frozenset([install_name_1, install_name_2])

        if not (self._package_to_results[install_name_1] and
                self._package_to_results[install_name_2]):
            return {
                'status': compatibility_store.Status.UNKNOWN.name,
                'self': True,
            }

        package_results = (
                self._package_to_results[install_name_1] +
                self._package_to_results[install_name_2])

        for pr in package_results:
            if pr.status != compatibility_store.Status.SUCCESS:
                return {
                    'status': pr.status.value,
                    'self': True,
                    'details': pr.details
                }

        if install_name_1 != install_name_2:
            pairwise_results = self._pairwise_to_results[install_names]
            if not pairwise_results:
                return {
                    'status': compatibility_store.Status.UNKNOWN.name,
                    'self': False,
                }
            for pr in pairwise_results:
                if pr.status != compatibility_store.Status.SUCCESS:
                    return {
                        'status': pr.status.value,
                        'self': False,
                        'details': pr.details
                    }
            return {
                'status': compatibility_store.Status.SUCCESS.name,
                'self': False,
            }
        return {
            'status': compatibility_store.Status.SUCCESS.name,
            'self': True,
        }


class GridBuilder:
    def __init__(self, store: compatibility_store.CompatibilityStore):
        self._store = store

    def build_grid(self, packages: Iterable[package.Package]) -> str:
        packages = list(packages)
        package_to_results = {}
        for p in packages:
            package_to_results[p.install_name] = list(
                self._store.get_self_compatibility(p))

        pairwise_to_results = {}
        for package_1, package_2 in itertools.combinations(packages, 2):
            install_names = frozenset(
                [package_1.install_name, package_2.install_name])
            pairwise_to_results[install_names] = list(
                self._store.get_pair_compatibility([package_1, package_2]))

        results = _ResultHolder(package_to_results, pairwise_to_results)
        template = _JINJA2_ENVIRONMENT.get_template('grid-template.html')
        return template.render(packages=packages, results=results)


def main():
    parser = argparse.ArgumentParser(
        description='Display a grid show the dependency compatibility ' +
                    'between Python packages')
    parser.add_argument('--packages', nargs='+',
                        default=_DEFAULT_INSTALL_NAMES,
                        help='the packages to display compatibility ' +
                             'information for')
    args = parser.parse_args()

    store = compatibility_store.CompatibilityStore()
    grid_builder = GridBuilder(store)

    _, grid_path = tempfile.mkstemp(suffix='.html')
    print(grid_path)
    with open(grid_path, 'wt') as f:
        f.write(grid_builder.build_grid(
            (package.Package(install_name) for install_name in args.packages)))
    webbrowser.open_new_tab('file://' + grid_path)


if __name__ == '__main__':
    main()
