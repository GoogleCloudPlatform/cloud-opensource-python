# Copyright 2018, Google LLC
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

set -ev

# Build dashboard
function build_dashboard {
    python grid_builder.py > dashboard/index.html
    if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
      openssl aes-256-cbc -d -a -k "$GOOGLE_CREDENTIALS_PASSPHRASE" \
          -in credentials.json.enc \
          -out $GOOGLE_APPLICATION_CREDENTIALS
      python grid_builder.py > dashboard/index.html
    else
      echo "No credentials. Dashboard will not build."
    fi
    return $?
}

build_dashboard
