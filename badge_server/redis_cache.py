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
"""A key/value cache using Redis."""

import os
import json
from typing import Any

import redis


class RedisCache:

    def __init__(self):
        redis_host = os.environ.get('REDISHOST', '10.0.0.3')
        redis_port = int(os.environ.get('REDISPORT', 6379))
        self._redis_client = redis.StrictRedis(host=redis_host, port=redis_port)

    def get(self, name: str) -> Any:
        """Returns a Python value given a key. None if not found."""
        return json.loads(self._redis_client.get(name))

    def set(self, name: str, value: Any):
        """Sets a key name to any Python object."""
        return self._redis_client.set(name, json.loads(value))
