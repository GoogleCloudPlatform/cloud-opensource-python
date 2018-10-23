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

"""A key/value cache using Google Cloud Datastore."""

import json
from typing import Any

from google.cloud import datastore


class DatastoreCache:
    def __init__(self):
        self._datastore_client = datastore.Client()
        
    def get(self, name: str) -> Any:
        """Returns a Python value given a key. None if not found."""

        key = self._datastore_client.key('_Cache', name)
        e = self._datastore_client.get(key)
        if e is None:
            return None
        else:
            return json.loads(e['value'])

    def set(self, name: str, value: Any):
        """Sets a key name to any Python object."""
        key = self._datastore_client.key('_Cache', name)
        e = datastore.Entity(key, exclude_from_indexes=['value'])
        e.update(value=json.dumps(value))
        self._datastore_client.put(e)
