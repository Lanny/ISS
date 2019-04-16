# -*- coding: utf-8 -*-

from ISS.forms import *
from ISS.models import *

import tutils

class FormsTestCase(tutils.ForumConfigTestCase):
    forum_config = {'captcha_period': 0}

    def setUp(self):
        tutils.create_std_forums()
        self.tony = tutils.create_user(thread_count=1, post_count=1)
        self.forum = Forum.objects.all()[0]
        self.thread = Thread.objects.all()[0]

    def test_dupe_post(self):
        post_data = {
            'content': 'take put take put',
            'thread': self.thread.pk
        }

        form = NewPostForm(post_data, author=self.tony)
        self.assertTrue(form.is_valid())
        form.get_post().save()

        form = NewPostForm(post_data, author=self.tony)
        self.assertFalse(form.is_valid())

    def test_dupe_thread(self):
        thread_data = {
            'title': 'communicate?',
            'content': 'take put take put',
            'forum': self.forum.pk
        }

        form = NewThreadForm(thread_data, author=self.tony)
        self.assertTrue(form.is_valid())
        form.save(self.tony, '192.168.0.1')

        form = NewThreadForm(thread_data, author=self.tony)
        self.assertFalse(form.is_valid())
