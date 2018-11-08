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
#
# Contains three independent versions of Python:
#  - python 3.6: used to run the web application
#  - python 3.6.5: used for python3 pip installation (build from source)
#  - python 2.7.15: used for python2 pip installation (build from source)

FROM python:3.6

# Create /etc/timezone so the package `tzdata` won't prompt for time zone information.
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir /compatibility_checker
ADD compatibility_checker_server.py /compatibility_checker
ADD pip_checker.py /compatibility_checker

RUN pip3 install docker

EXPOSE 8888

CMD python ./compatibility_checker/compatibility_checker_server.py \
     --host=0.0.0.0 --port=8888
