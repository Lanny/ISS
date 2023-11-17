#!/usr/bin/env bash

/opt/ISS/src/manage.py migrate
/opt/ISS/src/manage.py runserver 0.0.0.0:8000
