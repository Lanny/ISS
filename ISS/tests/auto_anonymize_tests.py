import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from ISS.models import *
from ISS.tests import test_utils

class AutoAnonymizeTestCase(TestCase):
    def setUp(self):
        self.scrub = Poster(username=u'scrub')
        self.aa1 = Poster(username=u'Autoanonymizer One')
        self.aa2 = Poster(username=u'Autoanonymizer Two')

        self.scrub.save()
        self.aa1.save()
        self.aa2.save()

        self.forum = Forum(name='test forum')
        self.forum.save()

        self.thread = Thread(
            title="test thread",
            forum=self.forum,
            author=self.scrub)
        self.thread.save()

        self.post = Post(
            author=self.scrub,
            content='foo bar',
            thread = self.thread)
        self.post.save()

        Thanks.objects.create(
            thanker=self.aa1,
            thankee=self.scrub,
            post=self.post)

        Thanks.objects.create(
            thanker=self.aa2,
            thankee=self.scrub,
            post=self.post)

    def test_thanks_deduplication(self):
        self.assertEqual(self.post.thanks_set.count(), 2)

        junk_user = Poster.get_or_create_junk_user()

        self.aa1.merge_into(junk_user)
        self.aa2.merge_into(junk_user)

        self.assertEqual(self.post.thanks_set.count(), 1)

        self.assertEqual(self.aa1.thanks_given.count(), 0)
        self.assertEqual(self.aa2.thanks_given.count(), 0)

        self.assertEqual(junk_user.thanks_given.count(), 1)


class AutoAnonymizeViewTestCase(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

    def test_younguns_cant_autoanonymize(self):
        tu = test_utils.create_user(1, 151)
        client = Client()
        client.force_login(tu)
        url = reverse('auto-anonymize')
        response = client.post(url)

        self.assertEqual(response.status_code, 403)

    def test_newbs_cant_autoanonymize(self):
        tu = test_utils.create_user(1, 5)
        tu.date_joined = timezone.now() - datetime.timedelta(days=365)
        tu.save()

        client = Client()
        client.force_login(tu)
        url = reverse('auto-anonymize')
        response = client.post(url)

        self.assertEqual(response.status_code, 403)

    def test_well_aged_users_can_autoanonymize(self):
        tu = test_utils.create_user(1, 151)
        tu.date_joined = timezone.now() - datetime.timedelta(days=365)
        tu.save()

        client = Client()
        client.force_login(tu)
        url = reverse('auto-anonymize')
        response = client.post(url)

        self.assertEqual(response.status_code, 302)
