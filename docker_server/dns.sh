#!/bin/bash

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

# Setup a DNS entry "docker.gcp.pycompatibility.dev" to make the docker
# group addressable.

set -e
set -x

gcloud beta dns managed-zones create gcp-zone \
  --dns-name=gcp.pycompatibility.dev \
  --description="An internal zone used by communication only within GCP." \
  --visibility=private \
  --networks=default

gcloud dns record-sets transaction start -z=gcp-zone

gcloud dns record-sets transaction add \
  -z=gcp-zone \
  --name=docker.gcp.pycompatibility.dev \
  --type=A \
  --ttl=300 \
  "10.128.15.195"

gcloud dns record-sets transaction execute -z=gcp-zone