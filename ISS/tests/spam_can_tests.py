from django.test import TestCase, Client
from django.urls import reverse
from ISS.models import *

class SpamCanTestCase(TestCase):
    def setUp(self):
        self.bot = Poster(username='bot')
        self.admin = Poster(username='admin', is_staff=True)

        self.bot.save()
        self.admin.save()

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


    def test_users_cant_access_form(self):
        path = reverse('spam-can-user', args=(self.bot.pk,))
        response = self.bot_client.get(path)
        self.assertEqual(response.status_code, 403)
