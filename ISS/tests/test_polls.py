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

        self.thread = tutils.create_thread(
            author=self.dahl,
            title='a thread with a poll',
            forum=Forum.objects.all()[0]
        )

        self.dahl_client = Client()
        self.dahl_client.force_login(self.dahl)

        self.lefkowitz_client = Client()
        self.lefkowitz_client.force_login(self.lefkowitz)

    def _create_poll(self, form_data={}, options=None, client=None):
        path = reverse('create-poll', kwargs={'thread_id': self.thread.pk})
        data = {
            'thread': self.thread.pk,
            'vote_type': '0',
            'question': 'Was EPOLL a good idea?',
        }

        data.update(form_data)

        if options is not None:
            data.update(options)
        else:
            data.update({
                'option-3': 'Yes',
                'option-5': 'No'
            })

        if not client:
            client = self.dahl_client

        return client.post(path, data)

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
        response = self._create_poll()
        self.assertIsNotNone(self.thread.poll)
        self.assertEqual(self.thread.poll.polloption_set.all().count(), 2)
        self.assertRedirects(
            response,
            self.thread.get_url(),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

    def test_polls_must_have_at_least_two_options(self):
        response = self._create_poll(options={})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_authors_cant_add_multiple_polls(self):
        self._create_poll()

        path = reverse('create-poll', kwargs={'thread_id': self.thread.id})
        response = self.dahl_client.get(path)
        self.assertEqual(response.status_code, 403)

        response = self._create_poll()
        self.assertEqual(response.status_code, 403)
