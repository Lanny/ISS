from datetime import timedelta

from django.test import TestCase
from django.test import SimpleTestCase
from ISS.models import *

import test_utils

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

class PostTestCase(test_utils.ForumConfigTestCase):
    forum_config = {
        'ninja_edit_grace_time': 120
    }

    def setUp2(self):
        test_utils.create_std_forums()
        self.rikimaru = test_utils.create_user(thread_count=1, post_count=0)
        self.post = self.rikimaru.post_set.all()[0]
        self.post.created = self.post.created - timedelta(days=4)
        self.post.has_been_edited = True
        self.post.save()

    def _edit_post(self, seconds_later):
        PostSnapshot.objects.create(
            post = self.post,
            time = self.post.created + timedelta(seconds=seconds_later),
            content = "something moody about heaven's wrath or whatever",
            obsolesced_by = self.rikimaru)

    def test_ninja_edit(self):
        self._edit_post(10)
        self.assertFalse(self.post.show_edit_line())
    
    def test_non_ninja_edit(self):
        self._edit_post(200)
        self.assertTrue(self.post.show_edit_line())
    
class PosterUsernameNormalizationTestCase(SimpleTestCase):
    def assertNormEqual(self, username_one, username_two):
        return self.assertEqual(
                Poster.normalize_username(username_one),
                Poster.normalize_username(username_two))

    def test_capitalization(self):
        self.assertNormEqual(u'Lanny', u'lanny')

    def test_spaces(self):
        self.assertNormEqual(u'Don Knuth', u'Don Knuth')

    def test_mixed_white_space(self):
        self.assertNormEqual(u'Don Knuth', u'D on\tKnuth\n\n')

    def test_mixed_white_space_and_caps(self):
        self.assertNormEqual(u'Don Knuth', u'd On\tknuTh\n\n')

    def test_homoglyph_attack(self):
        self.assertNormEqual(u'\u216Canny', u'Lanny')

    def test_case_sensitive_homoglyphs(self):
        self.assertNormEqual(u'Willard Quine', u'willard quine')

class SubscriptionTestCase(TestCase):
    def setUp(self):
        test_utils.create_std_forums()

        self.tu_1 = test_utils.create_user(thread_count=1)
        self.tu_2 = test_utils.create_user()

        self.thread = Thread.objects.filter(author=self.tu_1)[0]
        self.thread.subscribe(self.tu_1)
        self.thread.mark_read(self.tu_1)

    def _mkpost(self):
        post = Post(author=self.tu_2,
                    content='lorem ipsum',
                    thread=self.thread,
                    posted_from='8.8.8.4')
        post.save()

        return post

    def test_subscription_no_update(self):
        self.assertFalse(self.thread.has_unread_posts(self.tu_1))

    def test_subscription_with_update(self):
        self._mkpost()
        self.assertTrue(self.thread.has_unread_posts(self.tu_1))

    def test_subscription_after_delete(self):
        post = self._mkpost()
        op = self.thread.get_posts_in_thread_order()[0]
        self.assertTrue(self.thread.has_unread_posts(self.tu_1))
        
        self.thread.mark_read(self.tu_1)
        self.assertFalse(self.thread.has_unread_posts(self.tu_1))

        post.delete()

        self.assertTrue(self.thread.is_subscribed(self.tu_1))
        self.assertFalse(self.thread.has_unread_posts(self.tu_1))
        self.assertEqual(self.thread._get_flag(self.tu_1).last_read_post.pk,
                         op.pk)

    def test_subscription_after_multi_add_then_delete(self):
        first_post = self._mkpost()
        second_post = self._mkpost()
        op = self.thread.get_posts_in_thread_order()[0]

        self.assertTrue(self.thread.has_unread_posts(self.tu_1))

        second_post.delete()

        self.assertTrue(self.thread.is_subscribed(self.tu_1))
        self.assertTrue(self.thread.has_unread_posts(self.tu_1))
        self.assertEqual(self.thread._get_flag(self.tu_1).last_read_post.pk,
                         op.pk)

    def test_thread_get_jump_post(self):
        first_post = self._mkpost()
        second_post = self._mkpost()

        self.assertEqual(self.thread.get_jump_post(self.tu_1).pk, first_post.pk)

class ACLTestCase(TestCase):
    def setUp(self):
        self.tu_1 = test_utils.create_user()
        self.tu_2 = test_utils.create_user()
        self.tu_3 = test_utils.create_user()

        self.pacl = AccessControlList(name="PERM_ACL", allow_by_default=True)
        self.pacl.save()

        self.uacl = AccessControlList(name="UPERM_ACL", allow_by_default=False)
        self.uacl.save()

        self.non_even_group = AccessControlGroup(name="ODD_USERS")
        self.non_even_group.save()
        self.non_even_group.members.add(self.tu_1)
        self.non_even_group.members.add(self.tu_3)

    def test_default_permissive_list(self):
        self.assertTrue(self.pacl.is_poster_authorized(self.tu_1))

    def test_default_unpermissive_list(self):
        self.assertFalse(self.uacl.is_poster_authorized(self.tu_1))

    def test_blacklisted_case(self):
        self.pacl.black_posters.add(self.tu_1)
        self.assertFalse(self.pacl.is_poster_authorized(self.tu_1))
        self.assertTrue(self.pacl.is_poster_authorized(self.tu_2))

    def test_whitelisted_case(self):
        self.uacl.white_posters.add(self.tu_1)
        self.assertTrue(self.uacl.is_poster_authorized(self.tu_1))
        self.assertFalse(self.uacl.is_poster_authorized(self.tu_2))

    def test_group_whitelist_case(self):
        self.uacl.white_groups.add(self.non_even_group)
        self.assertTrue(self.uacl.is_poster_authorized(self.tu_1))
        self.assertTrue(self.uacl.is_poster_authorized(self.tu_3))
        self.assertFalse(self.uacl.is_poster_authorized(self.tu_2))

    def test_group_blacklist_case(self):
        self.pacl.black_groups.add(self.non_even_group)
        self.assertFalse(self.pacl.is_poster_authorized(self.tu_1))
        self.assertFalse(self.pacl.is_poster_authorized(self.tu_3))
        self.assertTrue(self.pacl.is_poster_authorized(self.tu_2))

    def test_user_primacy_over_group(self):
        self.uacl.white_posters.add(self.tu_3)
        self.uacl.black_groups.add(self.non_even_group)
        self.assertTrue(self.pacl.is_poster_authorized(self.tu_3))

    def test_get_acl(self):
        invite_acl = AccessControlList.get_acl('CREATE_INVITE')
        invite_group = AccessControlGroup.get_acg('INVITORS')
        invite_group.members.add(self.tu_1)

        self.assertTrue(invite_acl.is_poster_authorized(self.tu_1))
        self.assertFalse(invite_acl.is_poster_authorized(self.tu_2))
