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

RUN pip3 install docker requests

EXPOSE 8888

CMD python ./compatibility_checker/compatibility_checker_server.py \
     --host=0.0.0.0 --port=8888
