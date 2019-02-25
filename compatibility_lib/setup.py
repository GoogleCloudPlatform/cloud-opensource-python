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

import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()


namespaces = ['compatibility_lib']


setuptools.setup(
    name="compatibility_lib",
    version="0.1.3",
    author="Cloud Python",
    description="A library to get and store the dependency compatibility "
                "status data to BigQuery.",
    long_description=long_description,
    license="Apache-2.0",
    include_package_data=True,
    url="https://github.com/GoogleCloudPlatform/cloud-opensource-python/tree/"
        "master/compatibility_lib",
    packages=setuptools.find_packages(),
    namespace_packages=namespaces,
    classifiers=(
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ),
)
