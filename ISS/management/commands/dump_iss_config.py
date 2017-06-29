import json
import sys
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from ISS import utils


class Command(BaseCommand):
    help = ('Outputs the ISS configuration options as JSON. Primarily useful '
            'for communicating settings to frontend code.')

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        json.dump(utils.get_config(),
                  sys.stdout,
                  indent=2,
                  cls=utils.TolerantJSONEncoder)
