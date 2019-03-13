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
"""An in-memory key/value cache."""

from typing import Any


class FakeCache:

    def __init__(self):
        self._cache = {}

    def get(self, name: str) -> Any:
        """Returns a Python value given a key. None if not found."""
        return self._cache.get(name)

    def set(self, name: str, value: Any):
        """Sets a key name to any Python object."""
        self._cache[name] = value
