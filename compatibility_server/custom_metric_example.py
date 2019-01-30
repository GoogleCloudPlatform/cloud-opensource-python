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

"""Serves as an example of how to create and record custom metrics.

Note: This script relies on having authentication via Google Cloud SDK
See https://googleapis.github.io/google-cloud-python/latest/core/auth.html

After running this script, the metrics can be viewed on stackdriver
See https://app.google.stackdriver.com/metrics-explorer?project=python-compatibility-tools
"""

import random
import time
from pprint import pprint

from google.cloud import monitoring_v3
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats.exporters import stackdriver_exporter
from opencensus.tags import tag_map as tag_map_module

# create metrics
PROJECT_ID = 'python-compatibility-tools'

ERROR_MEASURE = measure_module.MeasureInt(
    'custom_test_error', 'The number of errors.', 'Errors')

# count aggregation
COUNT_VIEW = view_module.View(
    "testing_count_aggregation",
    "The number of errors",
    [],
    ERROR_MEASURE,
    aggregation_module.CountAggregation())

# distribution aggregation
# DISTRIBUTION_VIEW = view_module.View(
#     "testing_distribution_aggregation",
#     "The distribution of errors",
#     [],
#     ERROR_MEASURE,
#     aggregation_module.DistributionAggregation(
#         [0.0, 100.0]))

# LastValue Aggregation
# LAST_VALUE_VIEW = view_module.View(
#     "testing_last_value_aggregation",
#     "The last value of reported errors",
#     [],
#     ERROR_MEASURE,
#     aggregation_module.LastValueAggregation())

# sum aggregation
# SUM_VIEW = view_module.View(
#     "testing_sum_aggregation",
#     "The total number of errors",
#     [],
#     ERROR_MEASURE,
#     aggregation_module.SumAggregation())


def _enable_metrics(stats, view, export_to_stackdriver=True):
    view_manager = stats.view_manager
    if export_to_stackdriver:
        exporter = stackdriver_exporter.new_stats_exporter(
           stackdriver_exporter.Options(project_id=PROJECT_ID))
        view_manager.register_exporter(exporter)
    view_manager.register_view(view)


def _remove_from_stackdriver(project_id, view_name):
    client = monitoring_v3.MetricServiceClient()
    metric_url = 'custom.googleapis.com/opencensus/%s' % view_name
    name = 'projects/%s/metricDescriptors/%s' % (project_id, metric_url)
    client.delete_metric_descriptor(name)


stats = stats_module.Stats()
_enable_metrics(stats, COUNT_VIEW)
COUNT_MMAP = stats.stats_recorder.new_measurement_map()

# _enable_metrics(stats, DISTRIBUTION_VIEW)
# DISTRIBUTION_MMAP = stats.stats_recorder.new_measurement_map()

# _enable_metrics(stats, LAST_VALUE_VIEW)
# LAST_VALUE_MMAP = stats.stats_recorder.new_measurement_map()

# _enable_metrics(stats, SUM_VIEW)
# SUM_MMAP = stats.stats_recorder.new_measurement_map()

TMAP = tag_map_module.TagMap()

results = [random.randint(0, 1) for _ in range(100)]
for res in results:
    if res == 1:
        COUNT_MMAP.measure_int_put(ERROR_MEASURE, 1)
        COUNT_MMAP.record(TMAP)
        # DISTRIBUTION_MMAP.record(TMAP)
        # LAST_VALUE_MMAP.record(TMAP)
        # SUM_MMAP.record(TMAP)

view_names = [
    'testing_count_aggregation',
    # 'testing_distribution_aggregation',
    # 'testing_last_value_aggregation',
    # 'testing_sum_aggregation'
]

# Print the metrics
for view_name in view_names:
    view_data = stats.view_manager.get_view(view_name)
    pprint(vars(view_data))
    for k, v in view_data._tag_value_aggregation_data_map.items():
        pprint(k)
        pprint(vars(v))

# Need extra time to create the metric in order for it to be deleted without
# exceptions
time.sleep(300)

# Remove metrics from stackdriver
for view_name in view_names:
    _remove_from_stackdriver(PROJECT_ID, view_name)
