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

    def handle(self, **kwargs):
        for poster in Poster.objects.all().iterator():
            normed = Poster.normalize_username(poster.username)
            poster.normalized_username = normed
            poster.save()

        encountered_pks = set([])
        for poster in Poster.objects.all().iterator():
            if poster.pk in encountered_pks:
                continue

            normed = Poster.normalize_username(poster.username)
            dupes = Poster.objects.filter(normalized_username=normed)
            if len(dupes) > 1:
                print ('Duplicate normalized username found. Select the user '
                       'who should remain able to log in.')

                for idx, dupe in enumerate(dupes):
                    print '%d. "%s" (posts: %d, pk: %d)' % (
                            idx+1,
                            repr(dupe.username),
                            dupe.post_set.count(),
                            dupe.pk)

                i = None
                while type(i) != int or i > len(dupes) or i < 1:
                    try:
                        i = int(raw_input('>'))
                    except ValueError:
                        pass

                for idx, dupe in enumerate(dupes):
                    encountered_pks.add(dupe.pk)
                    if idx != i-1:
                        dupe.normalized_username = normed + str(idx)
                        dupe.save()
                        print Poster.objects.get(pk=dupe.pk).normalized_username

                true_user = dupes[i-1]
                true_user.normalized_username = normed
                true_user.save()

        print 'Done.'

