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

FROM ubuntu:18.04

WORKDIR "/tmp"

# Create /etc/timezone so the package `tzdata` won't prompt for time zone information.
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get --quiet=2 update && \
    apt-get --quiet=2 install --no-install-recommends \
        build-essential \
        curl \
        git \
        libbz2-dev \
        libncurses5-dev \
        libgdbm-dev \
        liblzma-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        openssl \
        python3.6 \
        python3-distutils \
        python3-pip \
        python3-setuptools \
        software-properties-common \
        tk-dev \
        xz-utils \
        zlib1g-dev \
        >/dev/null && \
    apt-get --quiet=2 clean && \
    rm -rf /var/lib/apt/lists/*

# Install an independent a pristine version of Python 3.6 for dependency
# testing.
RUN curl -s -S -O https://www.python.org/ftp/python/3.6.5/Python-3.6.5.tgz && \
  tar -xzf Python-3.6.5.tgz && \
  rm Python-3.6.5.tgz
WORKDIR /tmp/Python-3.6.5
RUN ./configure --prefix=/compatibility-checker >/dev/null
RUN make >make.out
RUN ! grep -A 2 "to build these optional modules were not found" make.out || \
  echo "\e[30;41m >>> There are known missing modules for Python 3.6 <<< \e[0m"
RUN make install >/dev/null
RUN make distclean >/dev/null
WORKDIR /tmp
RUN rm -rf /tmp/Pyt/tmp/Python-3.6.5

# Install an independent a pristine version of Python 2.7 for dependency
# testing.
RUN curl -s -S -O https://www.python.org/ftp/python/2.7.15/Python-2.7.15.tgz \
  && tar -xzf Python-2.7.15.tgz && \
  rm Python-2.7.15.tgz
WORKDIR /tmp/Python-2.7.15
RUN ./configure --prefix=/compatibility-checker >/dev/null
RUN make >make.out
RUN ! grep -A 2 "to build these optional modules were not found" make.out
RUN make install >/dev/null
RUN make distclean >/dev/null
WORKDIR /tmp
RUN rm -rf /tmp/Python-2.7.15

# Install pip in the two Python versions used for dependency testing.
RUN curl -s -S -O https://bootstrap.pypa.io/get-pip.py && \
  /compatibility-checker/bin/python2.7 get-pip.py && \
  /compatibility-checker/bin/python3.6 get-pip.py && \
  rm get-pip.py

COPY compatibility_checker_server.py /compatibility-checker
COPY pip_checker.py /compatibility-checker

EXPOSE 8888

ARG EXTRA_COMMAND_ARGUMENTS=""
ENV EXTRA_COMMAND_ARGUMENTS ${EXTRA_COMMAND_ARGUMENTS}

CMD python3 /compatibility-checker/compatibility_checker_server.py \
     --host=0.0.0.0 --port=8888 \
     ${EXTRA_COMMAND_ARGUMENTS} \
     --python-version \
     2:/compatibility-checker/bin/python2.7,3:/compatibility-checker/bin/python3.6

