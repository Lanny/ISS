import datetime

from django.test import TestCase, Client
from django.urls import reverse

from ISS import utils as iss_utils
from ISS import models as iss_models
from ISS.tests import test_utils
from ISS.contrib.taboo.models import *
from apps import TabooConfig

EXT = TabooConfig.name

iss_utils.get_ext_config(EXT)['min_posts_to_reg'] = 0
iss_utils.get_ext_config(EXT)['min_age_to_reg'] = datetime.timedelta(days=0)

class TabooModelsTest(TestCase):
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

    def test_post_save_handler(self):
        thread = iss_models.Thread.objects.all()[0]
        post_content = 'this is fOObar man'
        post = iss_models.Post.objects.create(
            author=self.mark,
            content=post_content,
            thread=thread)
        post = iss_models.Post.objects.get(pk=post.pk)

        self.assertTrue(self.mark.is_banned())
        self.assertTrue(post_content in post.content)
        self.assertTrue(post_content != post.content)

    def test_record_generated(self):
        thread = iss_models.Thread.objects.all()[0]
        post_content = 'this is fOObar man'
        post = iss_models.Post.objects.create(
            author=self.mark,
            content=post_content,
            thread=thread)

        self.assertEqual(self.profile.get_successes().count(), 1)

        vrecord = self.profile.get_successes[-1]
        self.assertEqual(vrecord.mark.pk, self.mark.pk)
        self.assertEqual(vrecord.poster.pk, self.assassin.pk)
        self.assertEqual(crecord.violating_post.pk, post.pk)

    def test_usertitle_change(self):
        thread = iss_models.Thread.objects.all()[0]
        post_content = 'this is fOObar man'
        post = iss_models.Post.objects.create(
            author=self.mark,
            content=post_content,
            thread=thread)

        self.mark = iss_models.Poster.objects.get(pk=self.mark.pk)
        self.assassin = iss_models.Poster.objects.get(pk=self.assassin.pk)

        self.assertEqual(self.mark.custom_user_title,
                         iss_utils.get_ext_config(EXT, 'usertitle_punishment'))
        self.assertEqual(self.assassin.custom_user_title,
                         iss_utils.get_ext_config(EXT, 'usertitle_reward'))


class TabooViewTest(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.tu_1 = test_utils.create_user(thread_count=1)
        self.tu_1_client = Client()
        self.tu_1_client.force_login(self.tu_1)
        
        self.tu_2 = test_utils.create_user()
        self.tu_2_client = Client()
        self.tu_2_client.force_login(self.tu_2)

        self.anon_client = Client()

    def test_must_be_logged_in(self):
        path = reverse('taboo-status')
        response = self.anon_client.get(path)
        self.assertEqual(response.status_code, 302)

    def test_unregistred_may_load(self):
        path = reverse('taboo-status')
        response = self.tu_1_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_register_once(self):
        path = reverse('taboo-register')
        response = self.tu_1_client.post(path, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TabooProfile.objects.all().count(), 1)

        prof = TabooProfile.objects.all()[0]
        self.assertEqual(prof.poster.pk, self.tu_1.pk)
        self.assertEqual(prof.mark, None)

    def test_register_twice(self):
        path = reverse('taboo-register')
        response = self.tu_1_client.post(path, {})
        self.assertEqual(response.status_code, 302)

        response = self.tu_2_client.post(path, {})
        self.assertEqual(response.status_code, 302)

        self.assertEqual(TabooProfile.objects.all().count(), 2)
        self.assertEqual(self.tu_1.taboo_profile.mark.pk, self.tu_2.pk)
        self.assertEqual(self.tu_2.taboo_profile.mark.pk, self.tu_1.pk)

    def test_unregister(self):
        self.tu_3 = test_utils.create_user()

        tu_3_profile = TabooProfile.objects.create(
            poster=self.tu_3,
            mark=self.tu_1,
            phrase='foobar')
        
        tu_2_profile = TabooProfile.objects.create(
            poster=self.tu_2,
            mark=self.tu_3,
            phrase='foobar')

        tu_1_profile = TabooProfile.objects.create(
            poster=self.tu_1,
            mark=self.tu_2,
            phrase='foobar')
 
        path = reverse('taboo-unregister')
        response = self.tu_1_client.post(path, {})
        self.assertEqual(response.status_code, 302)

        tu_1_profile = TabooProfile.objects.get(pk=tu_1_profile.pk)
        self.assertFalse(tu_1_profile.active)

        tu_3_profile = TabooProfile.objects.get(pk=tu_3_profile.pk)
        self.assertEqual(tu_3_profile.mark.pk, self.tu_2.pk)

    def test_quick_reregister(self):
        r_path = reverse('taboo-register')
        u_path = reverse('taboo-unregister')

        response = self.tu_1_client.post(r_path, {})
        self.assertEqual(response.status_code, 302)

        response = self.tu_1_client.post(u_path, {})
        self.assertEqual(response.status_code, 302)

        response = self.tu_1_client.post(r_path, {})
        self.assertEqual(response.status_code, 400)

    def test_slow_reregister(self):
        r_path = reverse('taboo-register')
        u_path = reverse('taboo-unregister')

        response = self.tu_1_client.post(r_path, {})
        self.assertEqual(response.status_code, 302)

        response = self.tu_1_client.post(u_path, {})
        self.assertEqual(response.status_code, 302)

        prof = TabooProfile.objects.get(poster=self.tu_1)
        prof.last_registration -= datetime.timedelta(days=42)

        response = self.tu_1_client.post(r_path, {})
