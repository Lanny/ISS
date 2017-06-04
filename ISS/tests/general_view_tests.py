from django.test import TestCase, Client
from django.urls import reverse
from ISS.models import *

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

