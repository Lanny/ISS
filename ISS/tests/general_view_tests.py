from django.test import TestCase, Client
from django.urls import reverse
from ISS.models import *

import test_utils

class GeneralViewTestCase(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.scrub = test_utils.create_user(thread_count=5, post_count=10)
        self.scrub.save()

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

