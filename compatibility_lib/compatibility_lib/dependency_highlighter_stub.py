# Copyright 2019 Google LLC
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
"""A stub implementation of dependency_highlighter.DependencyHighlighter."""

from typing import List

from compatibility_lib import dependency_highlighter


class DependencyHighlighterStub:
    def __init__(self):
        self._outdated_dependencies = {}

    def check_package(self, package_name: str
                      ) -> List[dependency_highlighter.OutdatedDependency]:
        return self._outdated_dependencies.get(package_name, [])

    def set_outdated_dependencies(
            self, package_name: str, outdated_dependencies: List[
                dependency_highlighter.OutdatedDependency]):
        self._outdated_dependencies[package_name] = outdated_dependencies
