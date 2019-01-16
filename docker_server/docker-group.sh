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
set -x

gcloud beta compute instance-groups managed create docker-group \
  --base-instance-name=docker-group \
  --template=docker-instance-template-20190114-151227 \
  --size=1 \
  --zone=us-central1-f \
  --initial-delay=300

gcloud compute instance-groups managed set-autoscaling "docker-group" \
  --zone "us-central1-f" \
  --cool-down-period "60" \
  --max-num-replicas "10" \
  --min-num-replicas "3" \
  --target-cpu-utilization "0.1"

gcloud compute health-checks create tcp docker-health-check \
   --port=2375

gcloud compute backend-services create docker-service \
  --health-checks=docker-health-check \
  --protocol=TCP \
  --load-balancing-scheme=INTERNAL \
  --region=us-central1

gcloud compute backend-services add-backend docker-service \
  --instance-group=docker-group \
  --balancing-mode=CONNECTION \
  --instance-group-zone=us-central1-f \
  --region=us-central1

gcloud compute forwarding-rules create docker-fe \
  --backend-service=docker-service \
  --load-balancing-scheme INTERNAL \
  --region=us-central1 \
  --ports=2375

gcloud compute firewall-rules create fw-allow-health-checks \
    --action ALLOW \
    --direction INGRESS \
    --source-ranges 35.191.0.0/16,130.211.0.0/22 \
    --rules tcp
