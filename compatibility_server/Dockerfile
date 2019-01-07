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

# An image used to run a Python webserver that does compatibility checking
# between pip-installable packages.

FROM python:3.6

RUN mkdir /compatibility_checker
ADD compatibility_checker_server.py /compatibility_checker
ADD pip_checker.py /compatibility_checker
ADD configs.py /compatibility_checker
ADD requirements.txt /compatibility_checker

RUN pip3 install -r /compatibility_checker/requirements.txt
RUN pip3 install gunicorn

EXPOSE 8888

# Restart each worker periodically so that `auto_remove`
# (https://docker-py.readthedocs.io/en/stable/containers.html) has a chance to work.
CMD cd compatibility_checker && \
  gunicorn -b 0.0.0.0:8888 -w 4 --max-requests 20 --max-requests-jitter 10 --timeout 120 \
           compatibility_checker_server:app
