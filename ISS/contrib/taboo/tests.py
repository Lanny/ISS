from django.test import TestCase

from ISS import models as iss_models
from ISS.tests import test_utils
from ISS.contrib.taboo.models import *

class TabooProfileTest(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.mark = test_utils.create_user(thread_count=1)
        self.assassin = test_utils.create_user()

        self.profile = TabooProfile.objects.create(
            poster=self.assassin,
            mark=self.mark,
            phrase='foobar')

    def test_TabooProfile_dot_matches_post_wrong_author(self):
        post = iss_models.Post(
            author=self.assassin,
            content='foobar')

        self.assertFalse(self.profile.matches_post(post))

    def test_TabooProfile_dot_matches_post_wrong_content(self):
        post = iss_models.Post(
            author=self.mark,
            content='woobar')

        self.assertFalse(self.profile.matches_post(post))

    def test_TabooProfile_dot_matches_post_quoted_content(self):
        post = iss_models.Post(
            author=self.mark,
            content='[quote]foobar[/quote] woobar')

        self.assertFalse(self.profile.matches_post(post))


    def test_TabooProfile_dot_matches_post_matches(self):
        post = iss_models.Post(
            author=self.mark,
            content='this is fOObar man')

        self.assertTrue(self.profile.matches_post(post))


