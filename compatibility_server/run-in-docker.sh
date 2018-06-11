#!/bin/bash
#
# Run the compatilbity_checker_server locally.

set -e

docker build -t compatibility-image \
      --build-arg EXTRA_COMMAND_ARGUMENTS="--clean" \
      .
docker run -p 8888:8888 compatibility-image
