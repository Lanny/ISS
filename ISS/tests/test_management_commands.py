# -*- coding: utf-8 -*-

from django.test import TestCase
from django.utils import timezone

from ISS.models import *
from ISS.management.commands.check_db import Command as CheckDBCommand
from . import tutils

class CheckDBTestCase(TestCase):
    def setUp(self):
        tutils.create_std_forums()
        self.cmd = CheckDBCommand()

    def test_valid_thread_author(self):
        op = tutils.create_user(thread_count=1, post_count=1)
        poster = tutils.create_user(thread_count=0, post_count=1)
        self.assertEqual(self.cmd.check_thread_authors(), True)

    def test_invalid_thread_author(self):
        op = tutils.create_user(thread_count=1, post_count=1)
        poster = tutils.create_user(thread_count=0, post_count=1)

        thread = Thread.objects.all()[0]
        thread.author = poster
        thread.save()

        self.assertEqual(self.cmd.check_thread_authors(), False)
