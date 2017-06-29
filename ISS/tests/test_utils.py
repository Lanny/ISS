import random

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

def create_user(thread_count=0, post_count=0): 
    global USERS_CREATED
    global THREADS_CREATED

    USERS_CREATED += 1
    user = Poster(username=u'TEST_USER-%d' % USERS_CREATED)
    user.save()

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

    for _ in range(post_count):
        post = Post(
            author=user,
            thread=random.choice(Thread.objects.all()),
            content='postum ipsum',
            posted_from='8.8.8.8')
        post.save()

    return user
