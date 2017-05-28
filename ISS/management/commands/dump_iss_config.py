import json
import sys
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from ISS import utils


class Command(BaseCommand):
    help = ('Migrates a vBulletin 5 database to ISS. Source database location '
            'and credentials must be supplied, target database info is picked '
            'up from settings.py. NB: this process is only idempotent over '
            'the users table.')

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        json.dump(utils.get_config(),
                  sys.stdout,
                  indent=2,
                  cls=utils.TolerantJSONEncoder)
