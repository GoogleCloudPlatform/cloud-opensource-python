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

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import view as view_module

# docker error
DOCKER_ERROR_MEASURE = measure_module.MeasureInt(
    'docker_error', 'The number of docker errors.', 'Errors')
DOCKER_ERROR_VIEW = view_module.View(
    "docker_error_count",
    "The number of the docker errors",
    [],
    DOCKER_ERROR_MEASURE,
    aggregation_module.CountAggregation())

ALL_VIEWS = [
    DOCKER_ERROR_VIEW,
]
