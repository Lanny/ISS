#!/usr/bin/env bash

# Startup script for running as a docker container

/opt/ISS/src/manage.py collectstatic --no-input --clear
/opt/ISS/src/manage.py migrate
uwsgi $@
