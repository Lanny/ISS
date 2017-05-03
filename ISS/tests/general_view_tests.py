from django.test import TestCase, Client
from django.urls import reverse
from ISS.models import *

class GeneralViewTestCase(TestCase):
    def setUp(self):
        self.scrub = Poster(username='scrub')
        self.scrub.save()

        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)

        self.general_cat = Category(name='general')
        self.general_cat.save()

        self.trash_cat = Category(name='trash cat')
        self.trash_cat.save()

        self.forum = Forum(name='test forum', category=self.general_cat)
        self.forum.save()

        self.trash_forum = Forum(name='trash forum',
                                 is_trash=True,
                                 category=self.trash_cat)
        self.trash_forum.save()

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
