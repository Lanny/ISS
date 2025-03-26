#!/usr/bin/env bash

MAJOR=$(cat VERSION | sed -r 's/([0-9]+)\.([0-9]+)\.([0-9]+)/\1/')
MINOR=$(cat VERSION | sed -r 's/([0-9]+)\.([0-9]+)\.([0-9]+)/\1.\2/')
FULL=$(head -n 1 VERSION)

git diff-files --quiet
if [ $? -eq 1 ]; then
  echo "Uncomitted changes in git, bailing"
  exit 1
fi


git tag "v$FULL"
docker build \
  -t lannysport/iss:latest \
  -t lannysport/iss:$MAJOR \
  -t lannysport/iss:$MINOR \
  -t lannysport/iss:$FULL \
  .

docker push lannysport/iss:latest
docker push lannysport/iss:$MAJOR
docker push lannysport/iss:$MINOR
docker push lannysport/iss:$FULL

git push origin tag "v$FULL"
