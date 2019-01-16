#! /bin/bash

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

# Install and run dockerd such that it is available for access outside
# of the VM.

set -o errexit
set -e
set -x

(

# Wait for the the aptitude system to be available by waiting until
# no other process holds a lock.
function wait_for_apt() {
  while lsof /var/lib/dpkg/lock;
  do
    sleep 1
  done
}

# Retry a command that could fail because apt-* is holding a lock.
# Usage is `retry <retry count> command` e.g.
#    retry 5 apt-get install python
function retry {
  local retries=$1
  shift

  local count=0
  until "$@"; do
    exit=$?
    wait=$((2 ** $count))
    count=$(($count + 1))
    if [ $count -lt $retries ]; then
      echo "Retry $count/$retries exited $exit, retrying in $wait seconds..."
      wait_for_apt
      sleep $wait
    else
      echo "Retry $count/$retries exited $exit, no more retries left."
      return $exit
    fi
  done
  return 0
}

wait_for_apt
retry 5 sudo apt-get update -y
retry 5 sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
retry 5 sudo add-apt-repository -y \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
retry 5 sudo apt-get update -y
retry 5 sudo apt-get install -y docker-ce

# Get dockerd to listen on an interfaces so that it is accessable outside of
# the VM instance.
sudo mkdir -p /etc/systemd/system/docker.service.d/
sudo cat >/etc/systemd/system/docker.service.d/override.conf <<EOF
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --registry-mirror=https://mirror.gcr.io -H tcp://0.0.0.0
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker.service
) >/startup-script-log 2>&1
