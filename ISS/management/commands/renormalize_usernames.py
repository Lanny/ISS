import json
import sys
from datetime import datetime
from django.db import IntegrityError, transaction

from django.core.management.base import BaseCommand, CommandError

from ISS.models import Poster


class Command(BaseCommand):
    help = ('Regenerates the `normalized_username` field for ever user in the '
            'database. Blocks and waits for user interaction over stdin if '
            'two users have the same normalized username')

    def add_arguments(self, parser):
        pass

    @transaction.atomic
    def handle(self, **kwargs):
        for poster in Poster.objects.all().iterator():
            normed = Poster.normalize_username(poster.username)
            dupes = Poster.objects.filter(normalized_username=normed)

            if len(dupes) > 1:
                print ('Duplicate normalized username found. Select the user '
                       'who should remain able to log in.')

                for idx, dupe in enumerate(dupes):
                    print '%d. "%s" (%d)' % (idx+1, repr(dupe.username),
                                            dupe.post_set.count())

                i = None
                while type(i) != int or idx > len(dupes) or idx < 1:
                    try:
                        i = int(raw_input('>'))
                    except ValueError:
                        pass

                for idx, dupe in enumerate(dupes):
                    if idx == i+1:
                        dupe.normalized_username = normed
                        dupe.save()
                    else:
                        dupe.normalized_username = normed + str(idx)

            else:
                poster.normalized_username = normed
                poster.save()

        print 'Done.'
