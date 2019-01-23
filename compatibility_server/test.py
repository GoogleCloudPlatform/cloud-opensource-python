import time

from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.stats.exporters import stackdriver_exporter
from opencensus.tags import tag_map as tag_map_module

# create metrics
PROJECT_ID = 'python-compatibility-tools'
m_docker_error = measure_module.MeasureInt(
    'docker_error', 'The number of docker errors.', 'Errors')
stats = stats_module.Stats()
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

latency_view = view_module.View(
    "docker_error_distribution",
    "The distribution of the docker errors",
    [],
    m_docker_error,
    aggregation_module.DistributionAggregation(
        [0.0, 100.0]))

# enable metrics
exporter = stackdriver_exporter.new_stats_exporter(
    stackdriver_exporter.Options(project_id=PROJECT_ID))
view_manager.register_exporter(exporter)

view_manager.register_view(latency_view)
mmap = stats_recorder.new_measurement_map()
tmap = tag_map_module.TagMap()

results = ['pass', 'pass', 'error', 'pass', 'error']
for res in results:
    if res == 'error':
        mmap.measure_int_put(m_docker_error, 1)
        mmap.record(tmap)
        time.sleep(1)

pprint(vars(view_data))
for k, v in view_data._tag_value_aggregation_data_map.items():
    pprint(k)
    pprint(vars(v))
