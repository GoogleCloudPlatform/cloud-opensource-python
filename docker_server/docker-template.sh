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

set -e

timestamp=$(date "+%Y%m%d-%H%M%S")
gcloud compute instance-templates create docker-instance-template-${timestamp} \
  --machine-type=n1-standard-4 \
  --maintenance-policy=MIGRATE \
  --image=ubuntu-1804-lts-drawfork-shielded-v20181106 \
  --image-project=eip-images \
  --boot-disk-size=4000GB \
  --boot-disk-type=pd-standard \
  --boot-disk-device-name=docker-disk \
  --metadata-from-file startup-script=docker-startup.sh

