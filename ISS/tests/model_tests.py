from django.test import TestCase
from ISS.models import *

class PosterTestCase(TestCase):
    def setUp(self):
        self.lanny = Poster(username='Lanny')
        self.feallen = Poster(username='F.E. Allen')
        self.don_knuth = Poster(username='Donald Knuth')

        self.lanny.save()
        self.feallen.save()
        self.don_knuth.save()

        self.forum = Forum(name='test forum')
        self.forum.save()

        self.thread = Thread(
            title="test thread",
            forum=self.forum,
            author=self.lanny)
        self.thread.save()

        self.post = Post(
            author = self.lanny,
            content ='foo bar',
            thread = self.thread)
        self.post.save()

    def test_poster_get_alts(self):
        Post.objects.create(
            author = self.lanny,
            content = 'hangin out at my buddy Don\'s house, aww yeah',
            thread = self.thread,
            posted_from = '8.8.8.4')

        Post.objects.create(
            author = self.feallen,
            content = 'you guys must be close, huh?',
            thread = self.thread,
            posted_from = '8.8.8.8')

        Post.objects.create(
            author = self.don_knuth,
            content = 'you know it fran',
            thread = self.thread,
            posted_from = '8.8.8.4')

        lannys_alts = self.lanny.get_alts()
        dons_alts = self.don_knuth.get_alts()
        frans_alts = self.feallen.get_alts()

        self.assertEqual(len(lannys_alts), 1)
        self.assertEqual(len(dons_alts), 1)
        self.assertEqual(len(frans_alts), 0)

        self.assertEqual(lannys_alts[0]['poster'].pk, self.don_knuth.pk)
        self.assertEqual(lannys_alts[0]['addr'], '8.8.8.4')

        self.assertEqual(dons_alts[0]['poster'].pk, self.lanny.pk)
        self.assertEqual(dons_alts[0]['addr'], '8.8.8.4')
