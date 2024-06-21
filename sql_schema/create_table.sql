CREATE TABLE self_compatibility_status (install_name VARCHAR(200), status VARCHAR(20), py_version VARCHAR(1), timestamp TIMESTAMP, details TEXT, PRIMARY KEY (install_name, py_version));

CREATE TABLE pairwise_compatibility_status (install_name_lower VARCHAR(200), install_name_higher VARCHAR(200), status VARCHAR(20), py_version VARCHAR(1), timestamp TIMESTAMP, details TEXT, PRIMARY KEY (install_name_lower, install_name_higher, py_version));

CREATE TABLE release_time_for_dependencies (install_name VARCHAR(200), dep_name VARCHAR(200), installed_version VARCHAR(50), installed_version_time DATETIME, latest_version VARCHAR(50), latest_version_time DATETIME, is_latest BOOLEAN, timestamp TIMESTAMP, PRIMARY KEY (install_name, dep_name));
