import random

from django.test import TestCase

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
            for _ in xrange(count)]

    if bulk:
        Post.objects.bulk_create(posts)
    else:
        for post in posts:
            post.save()

def create_user(thread_count=0, post_count=0, acgs=()): 
    global USERS_CREATED
    global THREADS_CREATED

    USERS_CREATED += 1
    user = Poster(username=u'TEST_USER-%d' % USERS_CREATED)
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

def refresh_model(model):
    return type(model).objects.get(pk=model.pk)

class ForumConfigTestCase(TestCase):
    _stored_values = {}
    _setup_called = False
    forum_config = {}

    def setUp(self):
        if self._setup_called:
            raise Exception('tearDown wasn\'t called. tearDown most likely '
                            'errantly overridden')
        self._setup_called = True

        for key in self.forum_config:
            self._stored_values[key] = utils.get_config()[key]
            utils.get_config()[key] = self.forum_config[key]


        self.setUp2()

    def setUp2(self):
        pass

    def tearDown(self):
        if not self._setup_called:
            raise Exception('setUp wasn\'t called. setUp most likely '
                            'errantly overridden')
        self.setup_called = False

        for key in self._stored_values:
            utils.get_config()[key] = self._stored_values[key] 

        self.tearDown2()

    def tearDown2(self):
        pass
