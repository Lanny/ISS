# -*- coding: utf-8 -*-

from ISS.forms import *
from ISS.models import *

from . import tutils

class DedupeFormsTestCase(tutils.ForumConfigTestCase):
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

class RegistrationFormTestCase(tutils.ForumConfigTestCase):

    def test_valid_registration(self):
        form = RegistrationForm({
            'username': 'Jimmy',
            'email': 'jimmy@lannysport.net',
            'password1': 'p4ssw0rd',
            'password2': 'p4ssw0rd'
        })
        self.assertTrue(form.is_valid())

    def test_forbidden_name(self):
        form = RegistrationForm({
            'username': 'Wintermute',
            'email': 'wm@lannysport.net',
            'password1': 'p4ssw0rd',
            'password2': 'p4ssw0rd'
        })
        self.assertFalse(form.is_valid())

        errors = form.errors.as_data() 
        self.assertEqual(errors.keys(), {'username'})
        self.assertEqual(errors['username'][0].code, 'FORBIDDEN_USERNAME')

    def test_forbidden_name_w_newlines(self):
        username = 'Instant Bitcoin Payouts. $16863 Ready For You\r\n >>> https://script.google.com/macros/s/AKfycbz_xnlUaUlxIDn_8JCIrW1EG9wpFCb1OBgVEY4ME7yjzJqL4eUrwzAXVjEUxH88Ct1l/exec#\r\n <<< 8671643'
        form = RegistrationForm({
            'username': username,
            'email': 'not@spammer.biz',
            'password1': 'p4ssw0rd',
            'password2': 'p4ssw0rd'
        })
        self.assertFalse(form.is_valid())

        errors = form.errors.as_data() 
        self.assertEqual(errors.keys(), {'username'})
        self.assertEqual(errors['username'][0].code, 'FORBIDDEN_USERNAME_PATTERN')

    def test_forbidden_name_pattern(self):
        form = RegistrationForm({
            'username': 'Visit https://totally-legit.com for $$$',
            'email': 'prince_ibrahim@nigeria.gov',
            'password1': 'p4ssw0rd',
            'password2': 'p4ssw0rd'
        })
        self.assertFalse(form.is_valid())

        errors = form.errors.as_data() 
        self.assertEqual(errors.keys(), {'username'})
        self.assertEqual(errors['username'][0].code,
                         'FORBIDDEN_USERNAME_PATTERN')
