from django.test import TestCase, Client
from django.urls import reverse
from ISS.models import *

class SpamCanTestCase(TestCase):
    def setUp(self):
        self.bot = Poster(username='bot')
        self.admin = Poster(username='admin', is_staff=True)
        self.joe = Poster(username='joe')

        self.bot.save()
        self.admin.save()
        self.joe.save()

        self.forum = Forum(name='test forum')
        self.forum.save()

        self.trash_forum = Forum(name='trash forum', is_trash=True)
        self.trash_forum.save()

        self.legit_thread = Thread(
            title="amazing content inside",
            forum=self.forum,
            author=self.admin)
        self.legit_thread.save()

        self.admin_op = Post(
            author=self.admin,
            content='the nothing, nothings',
            thread = self.legit_thread)
        self.admin_op.save()

        self.joes_post = Post(
            author=self.joe,
            content='deep man, deep',
            thread = self.legit_thread)
        self.joes_post.save()

        self.legit_thread.subscribe(self.joe)

        self.admins_second_post = Post(
            author=self.admin,
            content='quantum mechanics make me morally superior to everyone.',
            thread = self.legit_thread)
        self.admins_second_post.save()

        self.spam_post = Post(
            author=self.bot,
            content='buy some shitty product yo',
            thread = self.legit_thread)
        self.spam_post.save()

        self.spam_thread = Thread(
            title="wow, CCNs, SSNs, GRE scores and your mom!",
            forum=self.forum,
            author=self.bot)
        self.spam_thread.save()

        self.spam_op = Post(
            author=self.bot,
            content='buy some shitty product yo',
            thread = self.spam_thread)
        self.spam_op.save()

        self.admin_client = Client()
        self.admin_client.force_login(self.admin)

        self.bot_client = Client()
        self.bot_client.force_login(self.bot)

    def _spamcan_bot(self):
        path = reverse('spam-can-user', args=(self.bot.pk,))
        response = self.admin_client.post(path, {
            'target_forum': self.trash_forum.pk,
            'poster': self.bot.pk,
            'next_page': '/'
        })

        return response

    def test_users_cant_access_form(self):
        path = reverse('spam-can-user', args=(self.bot.pk,))
        response = self.bot_client.get(path)
        self.assertEqual(response.status_code, 403)

    def test_it_works(self):
        response = self._spamcan_bot()
        self.assertEqual(response.status_code, 302)

        self.spam_post = Post.objects.get(pk=self.spam_post.pk)
        self.spam_thread = Thread.objects.get(pk=self.spam_thread.pk)
        self.assertNotEqual(self.spam_post.thread.pk, self.legit_thread.pk)
        self.assertEqual(self.spam_thread.forum.pk, self.trash_forum.pk)

    def test_it_doesnt_fuck_up_subscriptions_unread_case(self):
        self.assertTrue(self.legit_thread.has_unread_posts(self.joe))
        self._spamcan_bot()
        self.legit_thread = Thread.objects.get(pk=self.legit_thread.pk)
        self.assertTrue(self.legit_thread.has_unread_posts(self.joe))

    def test_it_doesnt_fuck_up_subscriptions_read_case(self):
        self.legit_thread.mark_read(self.joe)
        self._spamcan_bot()
        self.legit_thread = Thread.objects.get(pk=self.legit_thread.pk)
        self.assertFalse(self.legit_thread.has_unread_posts(self.joe))

    def test_it_creates_a_ban_record(self):
        response = self._spamcan_bot()
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.bot.bans.count(), 1)
        ban = self.bot.bans.all()[0]
        self.assertEqual(ban.end_date, None)
        self.assertTrue(ban.is_active())
