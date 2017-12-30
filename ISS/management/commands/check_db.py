from django.core.management.base import BaseCommand, CommandError

from ISS.models import *


class Command(BaseCommand):
    help = 'Runs some checks to ensure the DB is in a consistent state.'

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        valid = self.do_checks(noisy=True)

        if valid:
            print 'All checks passed!'
        else:
            print 'One or more DB integrity issues detected.'

    def do_checks(self, noisy=False):
        all_good = True
        all_good = all_good and self.check_thread_authors(noisy=noisy)

        return all_good

    def check_thread_authors(self, noisy=False):
        valid = True
        for thread in Thread.objects.all().iterator():
            first_post_author = thread.get_first_post().author 
            if first_post_author != thread.author:
                valid = False

                if noisy:
                    print '\n\n' + '=' * 30 + ' ERROR ' + '=' * 30
                    print ('Thread with id %d has author %r, but first post '
                           'was made by %r.\n\n') % (thread.id,
                                                     first_post_author,
                                                     thread.author)

        return valid
