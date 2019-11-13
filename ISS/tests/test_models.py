from datetime import timedelta

from django.test import TestCase
from django.test import SimpleTestCase
from ISS.models import *

import tutils

class PosterTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'title_ladder': (
            (5, 'Regular'),
            (3, 'Acolyte'),
            (0, 'Novice')
        )
    }

    def setUp2(self):
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

        self.lanny.invalidate_user_title_cache()

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

    def test_is_banned_positive(self):
        tutils.ban_user(self.lanny)
        self.assertTrue(self.lanny.is_banned())

    def test_is_banned_infinite(self):
        tutils.ban_user(self.lanny, duration=None)
        self.assertTrue(self.lanny.is_banned())

    def test_is_banned_negative(self):
        self.assertFalse(self.lanny.is_banned())

    def test_is_banned_expired(self):
        tutils.ban_user(self.lanny, start_expired=True)
        self.assertFalse(self.lanny.is_banned())

    def test_get_ban_reason(self):
        tutils.ban_user(self.lanny, reason='bad reason', duration='1m')
        tutils.ban_user(self.lanny, reason='good reason', duration='2m')
        tutils.ban_user(self.lanny, reason='shit reason', duration='1m 5s')

        self.assertEqual(self.lanny.get_ban_reason(), 'good reason')

    def test_get_longest_ban_multi_bans(self):
        short_ban = tutils.ban_user(self.lanny, duration='1m')
        long_ban = tutils.ban_user(self.lanny, duration='2m')
        mid_ban = tutils.ban_user(self.lanny, duration='1m 5s')

        self.assertEqual(self.lanny.get_longest_ban(), long_ban)

    def test_get_longest_ban_infinite(self):
        short_ban = tutils.ban_user(self.lanny, duration='1m')
        inf_ban = tutils.ban_user(self.lanny, duration=None)

        self.assertEqual(self.lanny.get_longest_ban(), inf_ban)

    def test_get_longest_ban_no_bans(self):
        self.assertEqual(self.lanny.get_longest_ban(), None)

    def test_get_user_title_no_posts(self):
        self.assertEqual(self.lanny.get_user_title(), 'Novice')

    def test_get_user_title_some_posts(self):
        tutils.create_posts(self.lanny, 3)
        self.assertEqual(self.lanny.get_user_title(), 'Acolyte')

    def test_get_user_title_many_posts(self):
        tutils.create_posts(self.lanny, 5)
        self.assertEqual(self.lanny.get_user_title(), 'Regular')

    def test_get_user_title_banned(self):
        tutils.ban_user(self.lanny, duration=None)
        self.assertEqual(self.lanny.get_user_title(), 'Novice (banned)')

    def test_get_user_title_inf_ban(self):
        tutils.ban_user(self.lanny, duration='1m')
        self.assertEqual(self.lanny.get_user_title(), 'Novice (banned)')

    def test_get_user_title_inactive(self):
        self.lanny.is_active = False
        self.lanny.invalidate_user_title_cache()
        self.assertEqual(self.lanny.get_user_title(), 'Novice')

class PostTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'ninja_edit_grace_time': 120
    }

    def setUp2(self):
        tutils.create_std_forums()
        self.rikimaru = tutils.create_user(thread_count=1, post_count=0)
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

    def test_suepruser_can_edit(self):
        superuser = tutils.create_user(acgs=('SUPERUSERS',))
        self.assertTrue(self.post.can_be_edited_by(superuser))

    def test_author_can_edit(self):
        self.assertTrue(self.post.can_be_edited_by(self.rikimaru))

    def test_non_author_cant_edit(self):
        non_author = tutils.create_user()
        self.assertFalse(self.post.can_be_edited_by(non_author))

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
        tutils.create_std_forums()

        self.tu_1 = tutils.create_user(thread_count=1)
        self.tu_2 = tutils.create_user()

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

        self.thread = Thread.objects.get(pk=self.thread.pk)

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
        self.tu_1 = tutils.create_user()
        self.tu_2 = tutils.create_user()
        self.tu_3 = tutils.create_user()

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
