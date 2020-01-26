from django.test import Client
from django.urls import reverse

from ISS.models import Thread, Forum, Ban, Poll, PollOption, PollVote
from . import tutils

class PollCreationTestCase(tutils.ForumConfigTestCase):
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

class PollVotingTestCase(tutils.ForumConfigTestCase):
    forum_config = {'captcha_period': 0}

    def setUp(self):
        tutils.create_std_forums()

        self.dahl = tutils.create_user()
        self.lefkowitz = tutils.create_user()

        # Single-vote
        self.sv_thread = tutils.create_thread(
            author=self.dahl,
            title='a thread with a poll',
            forum=Forum.objects.all()[0]
        )

        self.sv_poll = Poll.objects.create(
            thread=self.sv_thread,
            vote_type=Poll.SINGLE_CHOICE,
            question='Was EPOLL as good idea?'
        )

        self.yes_opt = PollOption.objects.create(
            poll=self.sv_poll,
            answer='Yes'
        )
        self.no_opt = PollOption.objects.create(
            poll=self.sv_poll,
            answer='No'
        )


        # Multi-vote
        self.mv_thread = tutils.create_thread(
            author=self.dahl,
            title='a thread with a poll',
            forum=Forum.objects.all()[0]
        )

        self.mv_poll = Poll.objects.create(
            thread=self.mv_thread,
            vote_type=Poll.MULTIPLE_CHOICE,
            question='Which languages are garbage?'
        )

        self.py_opt = PollOption.objects.create(
            poll=self.mv_poll,
            answer='Python'
        )
        self.perl_opt = PollOption.objects.create(
            poll=self.mv_poll,
            answer='Perl'
        )
        self.js_opt = PollOption.objects.create(
            poll=self.mv_poll,
            answer='Javascript'
        )

        self.dahl_client = Client()
        self.dahl_client.force_login(self.dahl)

        self.lefkowitz_client = Client()
        self.lefkowitz_client.force_login(self.lefkowitz)

    def _cast_single_vote(self, client, opt):
        path = reverse(
            'vote-on-poll',
            kwargs={'poll_id': self.sv_poll.pk}
        )
        return client.post(path, {'response': opt.pk})

    def _cast_multiple_vote(self, client, opts):
        path = reverse(
            'vote-on-poll',
            kwargs={'poll_id': self.mv_poll.pk}
        )
        return client.post(path, {'response': [opt.pk for opt in opts]})

    def test_poster_can_single_vote(self):
        response = self._cast_single_vote(self.dahl_client, self.yes_opt)

        self.assertRedirects(
            response,
            self.sv_thread.get_url(),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True)

        self.assertEqual(
                PollVote.objects
                    .filter(voter=self.dahl, poll_option=self.yes_opt)
                    .count(),
                1)

    def test_poster_can_multi_vote(self):
        pass

    def test_anon_poster_cant_vote(self):
        client = Client()
        response = self._cast_single_vote(client, self.yes_opt)
        self.assertEqual(PollVote.objects.all().count(), 0)

    def test_banned_poster_cant_vote(self):
        Ban.objects.create(
            subject=self.dahl,
            given_by=self.lefkowitz,
            reason='JS a shit')

        response = self._cast_single_vote(self.dahl_client, self.yes_opt)
        self.assertEqual(response.status_code, 403)

    def test_inactive_poster_cant_vote(self):
        self.dahl.is_active = False
        self.dahl.save()
        self._cast_single_vote(self.dahl_client, self.yes_opt)
        self.assertEqual(PollVote.objects.all().count(), 0)

    def test_poster_cant_double_vote(self):
        self._cast_single_vote(self.dahl_client, self.yes_opt)
        self._cast_single_vote(self.dahl_client, self.yes_opt)
        self.assertEqual(PollVote.objects.all().count(), 1)

    def test_poster_cant_empty_vote(self):
        path = reverse(
            'vote-on-poll',
            kwargs={'poll_id': self.sv_poll.pk}
        )
        self.dahl_client.post(path, {})
        self.assertEqual(PollVote.objects.all().count(), 0)

    def test_sv_vote_distribution(self):
        dist = self.sv_poll.get_vote_distribution()

        self.assertEqual(dist[self.yes_opt], 0)
        self.assertEqual(dist[self.no_opt], 0)

        self._cast_single_vote(self.dahl_client, self.yes_opt)
        self._cast_single_vote(self.lefkowitz_client, self.yes_opt)

        dist = self.sv_poll.get_vote_distribution()

        self.assertEqual(dist[self.yes_opt], 2)
        self.assertEqual(dist[self.no_opt], 0)
