#!/bin/bash
set -x

MODULEMD_TOOLS_TAG=${DOCKER_USERNAME:-}${DOCKER_USERNAME:+/}${MODULEMD_TOOLS_TAG:-modulemd_tools_tests}

if [ "$1" == "build" ]
then
  docker build -t $MODULEMD_TOOLS_TAG -f Dockerfile-tests .

# for later/integration testing
elif [ "$1" == "docker_push" ]
then
  set +x
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  set -x
  docker push $MODULEMD_TOOLS_TAG

# complementary stage for docker_pull
elif [ "$1" == "docker_pull" ]
then
  set +x
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  set -x
  docker pull $MODULEMD_TOOLS_TAG

elif [ "$1" == "test" ]
then
  docker run -e TOXENV -e SITEPACKAGES -e MODULEMD_TOOL \
             -v $TRAVIS_BUILD_DIR:/modulemd-tools $MODULEMD_TOOLS_TAG

fi
