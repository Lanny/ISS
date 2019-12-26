from django.core.management.base import BaseCommand
from django.core.management import call_command

from ISS.models import *


class Command(BaseCommand):
    help = 'Same as manage.py migrate && manage.py runserver'

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        call_command('migrate')
        call_command('runserver', '0.0.0.0:8000')
