import random
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from ISS import utils
from ISS.models import *

def create_std_forums():
    general_cat = Category(name='general')
    general_cat.save()

    trash_cat = Category(name='trash cat')
    trash_cat.save()

    forum = Forum(name='test forum', category=general_cat)
    forum.save()

    trash_forum = Forum(name='trash forum',
                             is_trash=True,
                             category=trash_cat)
    trash_forum.save()

USERS_CREATED = 0
THREADS_CREATED = 0

def create_post(user, thread, save=True):
    post = Post(
            author=user,
            thread=thread,
            content='postum ipsum',
            posted_from='8.8.8.8')

    if save:
        post.save()

    return post

def create_posts(user, count, bulk=False):
    """
    Create `count` posts belonging to `user`. Skips signal triggering if `bulk`
    is True which speeds things up but may cause unexpected behavior.
    """
    posts = [Post(
                author=user,
                thread=random.choice(Thread.objects.all()),
                content='postum ipsum',
                posted_from='8.8.8.8')
            for _ in range(count)]

    if bulk:
        Post.objects.bulk_create(posts)
    else:
        for post in posts:
            post.save()

def create_user(thread_count=0, post_count=0, username=None, acgs=()): 
    global USERS_CREATED
    global THREADS_CREATED

    USERS_CREATED += 1
    username = username or ('TEST_USER-%d' % USERS_CREATED)
    user = Poster(username=username)
    user.save()

    for acg in acgs:
        AccessControlGroup.get_acg(acg).members.add(user)

    for _ in range(thread_count):
        THREADS_CREATED += 1
        destination_forum = random.choice(Forum.objects.all())

        thread = Thread(
            title='TEST_THREAD-%d' % THREADS_CREATED,
            forum=destination_forum,
            author=user)
        thread.save()

        op = Post(
            author=user,
            thread=thread,
            content='opsum ipsum',
            posted_from='8.8.8.4')
        op.save()

    create_posts(user, post_count)

    return user

def ban_user(user, duration='1m', reason='test ban', start_expired=False):
    start_date = timezone.now()

    if duration != None:
        duration = utils.parse_duration(duration)
        if start_expired:
            start_date -= duration + timedelta(seconds=1)
        end_date = start_date + duration
    elif start_expired:
        raise RuntimeError(
            'It makes no sense to have an infinte duration ban but also '
            'start expired.')
    else:
        end_date=None


    ban = Ban(
        subject=user,
        given_by=Poster.get_or_create_system_user(),
        start_date=start_date,
        end_date=end_date,
        reason=reason)

    ban.save()
    return ban

def refresh_model(model):
    return type(model).objects.get(pk=model.pk)

class ForumConfigTestCase(TestCase):
    _stored_values = {}
    _setup_called = False
    forum_config = {}

    @classmethod
    def setUpClass(cls):
        super(ForumConfigTestCase, cls).setUpClass()
        cm = utils.ConfigurationManager.get_instance()
        config = utils.rmerge(settings.FORUM_CONFIG, cls.forum_config)
        cm.reinit(config)

        #for key in cls.forum_config:
        #    cls._stored_values[key] = utils.get_config()[key]
        #    utils.get_config()[key] = cls.forum_config[key]

    def setUp(self):
        cache.clear()
        self.setUp2()

    def tearDown(self):
        self.tearDown2()

    def setUp2(self):
        """
        Legacy method, use setUp in subclasses instead.
        """
        pass

    def tearDown2(self):
        """
        Legacy method, use tearDown in subclasses instead.
        """
        pass
