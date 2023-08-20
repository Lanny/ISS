import random

from django.core.management.base import BaseCommand, CommandError
from ISS.models import *

ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed id nisi magna. Ut faucibus metus nulla, non placerat est pellentesque auctor. Fusce in ligula ut lorem vehicula tincidunt sed eu urna. In sit amet lorem mattis, interdum massa sit amet, cursus ex. Donec non lacinia metus, at finibus ante. Donec at eros id eros porttitor lobortis id a justo. Phasellus consectetur, dui sit amet fringilla fermentum, sem tellus lacinia dui, sed aliquam mi magna rutrum sem. Etiam non tempus libero. Morbi dignissim lacus et odio volutpat gravida. Vivamus sit amet velit tortor. Maecenas tincidunt accumsan justo, sit amet pellentesque felis eleifend vel. Nullam venenatis lorem eget dolor porta, eget ultricies quam condimentum. Ut elementum volutpat elementum. Ut consectetur, arcu vitae interdum venenatis, magna dolor lobortis nibh, vel sollicitudin enim lectus ac felis. Duis sodales ullamcorper interdum".split(' ')

def gen_content():
    return ' '.join([random.choice(ipsum) for _ in range(random.randint(20,200))])

class Command(BaseCommand):
    help = 'Creates N new posts over existing threads by existing users.'

    def add_arguments(self, parser):
        parser.add_argument('n', type=int)

    def handle(self, *args, **kwargs):
        posters = Poster.objects.filter(is_active=True)
        threads = Thread.objects.filter(locked=False)

        for _ in range(kwargs.get('n', 0)):
            poster = random.choice(posters)
            thread = random.choice(threads)

            post = Post(thread=thread,
                        author=poster,
                        content=gen_content())

            post.save()


