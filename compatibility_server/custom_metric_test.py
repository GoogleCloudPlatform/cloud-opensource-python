import random
import time
from pprint import pprint

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats.exporters import stackdriver_exporter
from opencensus.tags import tag_map as tag_map_module

# create metrics
PROJECT_ID = 'python-compatibility-tools'

DOCKER_ERROR_MEASURE = measure_module.MeasureInt(
    'count_docker_error', 'The number of docker errors.', 'Errors')

# count aggregation
COUNT_VIEW = view_module.View(
    "docker_error_count",
    "The number of the docker errors",
    [],
    DOCKER_ERROR_MEASURE,
    aggregation_module.CountAggregation())

# distribution aggregation
DISTRIBUTION_VIEW = view_module.View(
    "docker_error_distribution",
    "The distribution of the docker errors",
    [],
    DOCKER_ERROR_MEASURE,
    aggregation_module.DistributionAggregation(
        [0.0, 100.0]))

# LastValue Aggregation
LAST_VALUE_VIEW = view_module.View(
    "docker_error_last_value",
    "The last value of the docker errors",
    [],
    DOCKER_ERROR_MEASURE,
    aggregation_module.LastValueAggregation())

# sum aggregation
SUM_VIEW = view_module.View(
    "docker_error_sum",
    "The total number of docker errors",
    [],
    DOCKER_ERROR_MEASURE,
    aggregation_module.SumAggregation())

def _enable_metrics(stats, view, export_to_stackdriver=True):
    view_manager = stats.view_manager
    if export_to_stackdriver:
        exporter = stackdriver_exporter.new_stats_exporter(
           stackdriver_exporter.Options(project_id=PROJECT_ID))
        view_manager.register_exporter(exporter)
    view_manager.register_view(view)


stats = stats_module.Stats()
_enable_metrics(stats, COUNT_VIEW)
COUNT_MMAP = stats.stats_recorder.new_measurement_map()

_enable_metrics(stats, DISTRIBUTION_VIEW)
DISTRIBUTION_MMAP = stats.stats_recorder.new_measurement_map()

_enable_metrics(stats, LAST_VALUE_VIEW)
LAST_VALUE_MMAP = stats.stats_recorder.new_measurement_map()

_enable_metrics(stats, SUM_VIEW)
SUM_MMAP = stats.stats_recorder.new_measurement_map()

TMAP = tag_map_module.TagMap()

for _ in range(1000):
    res = random.randint(0, 1)
    if res == 1:
        COUNT_MMAP.measure_int_put(DOCKER_ERROR_MEASURE, 1)
        COUNT_MMAP.record(TMAP)

        DISTRIBUTION_MMAP.measure_int_put(DOCKER_ERROR_MEASURE, 1)
        DISTRIBUTION_MMAP.record(TMAP)

        LAST_VALUE_MMAP.measure_int_put(DOCKER_ERROR_MEASURE, 1)
        LAST_VALUE_MMAP.record(TMAP)

        SUM_MMAP.measure_int_put(DOCKER_ERROR_MEASURE, 1)
        SUM_MMAP.record(TMAP)

view_names = ['docker_error_count',
              'docker_error_distribution',
              'docker_error_last_value',
              'docker_error_sum'
             ]
for view_name in view_names:
    view_data = stats.view_manager.get_view(view_name)
    pprint(vars(view_data))
    for k, v in view_data._tag_value_aggregation_data_map.items():
        pprint(k)
        pprint(vars(v))
