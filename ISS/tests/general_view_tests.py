import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from ISS.models import *
from ISS import utils
import test_utils

class GeneralViewTestCase(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.scrub = test_utils.create_user(thread_count=5, post_count=10)

        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)


    def test_authed_users_can_access_index(self):
        path = reverse('forum-index')
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_unauthed_users_can_access_index(self):
        path = reverse('forum-index')
        anon_client = Client()
        response = anon_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_index_has_categories(self):
        path = reverse('forum-index')
        response = self.scrub_client.get(path)
        self.assertEqual(len(response.context['categories']), 2)
        self.assertTrue(isinstance(response.context['forums_by_category'], dict))

    def test_threads_by_user(self):
        path = reverse('threads-by-user', kwargs={'user_id': self.scrub.pk})
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['threads']), 5)

    def test_user_profile_doesnt_error(self):
        path = reverse('user-profile', kwargs={'user_id': self.scrub.pk})
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)

class PostFloodControlTestCase(TestCase):
    def setUp(self):
        test_utils.create_std_forums()
        self.scrub = test_utils.create_user(thread_count=1, post_count=0)
        self.thread = Thread.objects.get(author=self.scrub)
        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)
        self.path = reverse('new-reply', args=(self.thread.pk,))
        self.limit = utils.get_config('initial_account_period_limit')

    def _attempt_new_post(self):
        prior_count = self.scrub.post_set.count()

        response = self.scrub_client.post(self.path, {
            'content': 'foobar!',
            'thread': self.thread.pk
        })

        return self.scrub.post_set.count() - prior_count

    def test_initial_account_period_compliance(self):
        # Post should be created
        self.assertEqual(self._attempt_new_post(), 1)

    def test_initial_account_period_violation(self):
        test_utils.create_posts(self.scrub, self.limit, bulk=True)
        # Post should be rejected
        self.assertEqual(self._attempt_new_post(), 0)

    def test_initial_account_period_violation_cooldown(self):
        test_utils.create_posts(self.scrub, self.limit, bulk=True)
        new_created = timezone.now() - utils.get_config(
                'initial_account_period_width')
        self.scrub.post_set.update(created=new_created)

        # Post should be created
        self.assertEqual(self._attempt_new_post(), 1)

    def test_initial_account_period_done(self):
        # Create enough posts to get us out of the initial period
        count = utils.get_config('initial_account_period_total')
        test_utils.create_posts(self.scrub, count + 1, bulk=True)

        self.assertEqual(self._attempt_new_post(), 1)

class ThreadActionTestCase(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.admin = test_utils.create_user()
        self.scrub = test_utils.create_user(thread_count=1, post_count=10)

        self.admin.is_admin = True
        self.admin.is_staff = True
        self.admin.save()

        self.thread = Thread.objects.all()[0]

        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)
        self.admin_client = Client()
        self.admin_client.force_login(self.admin)

    def test_non_staff_may_not_delete_posts(self):
        path = reverse('thread-action', kwargs={'thread_id': self.thread.pk})
        response = self.scrub_client.post(path, {'action': 'delete-posts'})
        self.assertEqual(response.status_code, 403)

    def test_staff_may_delete_posts(self):
        path = reverse('thread-action', kwargs={'thread_id': self.thread.pk})
        posts_to_delete = self.thread.post_set.order_by('-created')[8:]

        response = self.admin_client.post(path, {
            'action': 'delete-posts',
            'post': [p.pk for p in posts_to_delete]
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.thread.post_set.count(), 8)

class AdminThreadCreationForum(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.admin = test_utils.create_user()
        self.scrub = test_utils.create_user()

        self.admin.is_admin = True
        self.admin.is_staff = True
        self.admin.save()

        self.admin_client = Client()
        self.admin_client.force_login(self.admin)
        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)

        auth_package = AuthPackage.objects.create(
            logic_package='ADMIN_REQUIRED')

        self.admin_only_forum = Forum.objects.all()[0]
        self.admin_only_forum.create_thread_pack = auth_package
        self.admin_only_forum.save()

    def test_admin_may_make_thread(self):
        path = reverse('new-thread',
                       kwargs={'forum_id': self.admin_only_forum.pk})
        response = self.admin_client.post(path, {
            'title': 'Presenting: Admin made thread',
            'content': 'by admins, for everyone.',
            'forum': str(self.admin_only_forum.pk)
        })
        self.assertEqual(response.status_code, 302)

    def test_scrub_may_not_make_thread(self):
        path = reverse('new-thread',
                       kwargs={'forum_id': self.admin_only_forum.pk})
        response = self.scrub_client.post(path, {
            'title': 'this shouldn\'t go through',
            'content': 'if you\'re reading this something has gone wrong.',
            'forum': str(self.admin_only_forum.pk)
        })
        self.assertEqual(response.status_code, 403)

