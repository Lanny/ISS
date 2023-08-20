#!/usr/bin/env python
import os
import sys

def main():
    settings_file_path = os.environ.get("ISS_SETTINGS_FILE")

    if not settings_file_path:
        raise Exception("Must provide a `ISS_SETTINGS_FILE` env var")

    settings_dir, settings_file = os.path.split(settings_file_path)
    settings_mod_name = os.path.splitext(settings_file)[0]

    sys.path.append(os.path.abspath(settings_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_mod_name)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
