from django.test import Client
from django.urls import reverse

from ISS.models import Thread, Forum, Poll
from . import tutils

class PollsTestCase(tutils.ForumConfigTestCase):
    forum_config = {'captcha_period': 0}

    def setUp(self):
        tutils.create_std_forums()

        self.dahl = tutils.create_user()
        self.lefkowitz = tutils.create_user()

        self.thread = Thread.objects.create(
            title='a thread with a poll',
            forum=Forum.objects.all()[0],
            author=self.dahl)

        self.dahl_client = Client()
        self.dahl_client.force_login(self.dahl)

        self.lefkowitz_client = Client()
        self.lefkowitz_client.force_login(self.lefkowitz)

    def test_non_authors_cant_add_polls(self):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.lefkowitz_client.post(path, {})
        self.assertEqual(response.status_code, 403)
