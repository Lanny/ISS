"""
WSGI config for ISS project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

settings_file_path = os.environ.get("ISS_SETTINGS_FILE")

if not settings_file_path:
    raise Exception("Must provide a `ISS_SETTINGS_FILE` env var")

settings_dir, settings_file = os.path.split(settings_file_path)
settings_mod_name = os.path.splitext(settings_file)[0]

sys.path.append(os.path.abspath(settings_dir))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_mod_name)


application = get_wsgi_application()
