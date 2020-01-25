from django.test import Client
from django.urls import reverse

from ISS.models import Thread, Forum, Poll
from . import tutils

class PollsCreationTestCase(tutils.ForumConfigTestCase):
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

    def test_non_authors_cant_view_poll_add_view(self):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.lefkowitz_client.get(path)
        self.assertEqual(response.status_code, 403)

    def test_non_authors_cant_add_polls(self):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.lefkowitz_client.post(path, {})
        self.assertEqual(response.status_code, 403)

    def test_authors_can_view_poll_add_view(self):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.dahl_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_authors_can_add_polls(self):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.dahl_client.post(path, {
            'vote_type': '0',
            'question': 'Was EPOLL a good idea?',
            'options-3': 'Yes'
            'options-5': 'No'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(self.thread.poll)
        self.assertIsEqual(self.thread.poll.polloption_set.all().count(), 2)

    def test_authors_cant_add_multiple_polls(self):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.dahl_client.get(path)
        self.assertEqual(response.status_code, 403)

        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.dahl_client.post(path, {})
        self.assertEqual(response.status_code, 403)
