from django.core.management import BaseCommand, CommandError
from ISS.models import Poster


class Command(BaseCommand):
    help = 'Crate a superuser with no input'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--username', dest='username', default=None)
        parser.add_argument('--email', dest='email', default=None)
        parser.add_argument('--password', dest='password', default=None)

    def handle(self, *args, **options):
        password = options.get('password')
        email = options.get('email')
        username = options.get('username')

        if not (password and email and username):
            raise CommandError("All args required.")

        poster = Poster(
            is_staff=True,
            is_admin=True,
            is_superuser=True,
            username=username,
            email=email)
        poster.set_password(password)
        poster.save()
