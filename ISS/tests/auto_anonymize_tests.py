from django.test import TestCase
from ISS.models import *

class AutoAnonymizeTestCase(TestCase):
    def setUp(self):
        self.scrub = Poster(username='scrub')
        self.aa1 = Poster(username='Autoanonymizer One')
        self.aa2 = Poster(username='Autoanonymizer Two')

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
