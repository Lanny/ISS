# -*- coding: utf-8 -*-

import datetime
import json

from django.conf import settings
from django.core import mail
from django.contrib.auth import authenticate, get_user
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone

from ISS.models import *
from ISS import utils
from . import tutils

class GeneralViewTestCase(tutils.ForumConfigTestCase):
    forum_config = {'captcha_period': 0}

    def setUp(self):
        tutils.create_std_forums()

        self.scrub = tutils.create_user(thread_count=5, post_count=10)
        self.scrub.auto_subscribe = 1
        self.scrub.save()

        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)


    def test_authed_users_can_access_index(self):
        path = reverse('forum-index')
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_unauthed_users_can_access_index(self):
        path = reverse('forum-index')
        anon_client = Client()
        response = anon_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_index_has_categories(self):
        path = reverse('forum-index')
        response = self.scrub_client.get(path)
        self.assertEqual(len(response.context['categories']), 2)
        self.assertTrue(isinstance(response.context['forums_by_category'], dict))

    def test_threads_by_user(self):
        path = reverse('threads-by-user', kwargs={'user_id': self.scrub.pk})
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['threads']), 5)

    def test_user_profile_doesnt_error(self):
        path = reverse('user-profile', kwargs={'user_id': self.scrub.pk})
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        thread = Thread.objects.all()[0]
        path = reverse('new-reply', kwargs={'thread_id': thread.pk})
        post_count = self.scrub.get_post_count()
        response = self.scrub_client.post(path, {
            'content': 'P = NP?',
            'thread': thread.pk
        })
        self.assertEqual(self.scrub.get_post_count(), post_count + 1)

    def test_new_post_too_long(self):
        thread = Thread.objects.all()[0]
        path = reverse('new-reply', kwargs={'thread_id': thread.pk})
        post_count = self.scrub.get_post_count()
        response = self.scrub_client.post(path, {
            'content': 'P = NP?' * 3000,
            'thread': thread.pk
        })
        self.assertEqual(self.scrub.get_post_count(), post_count)

    def test_new_thread(self):
        forum = Forum.objects.all()[0]
        path = reverse('new-thread', kwargs={'forum_id': forum.pk})

        response = self.scrub_client.post(
            path,
            {
                'title': 'SAT is a lie',
                'content': 'NP erect lol',
                'forum': forum.pk
            })

        self.assertEqual(response.status_code, 302)

    def test_new_thread_generates_subscription(self):
        forum = Forum.objects.all()[0]
        path = reverse('new-thread', kwargs={'forum_id': forum.pk})

        response = self.scrub_client.post(
            path,
            {
                'title': 'SAT is a lie',
                'content': 'NP erect lol',
                'forum': forum.pk
            })

        match = resolve(response['Location'])
        thread = Thread.objects.get(pk=match.kwargs['thread_id'])

        subscription = ThreadFlag.objects.get(poster=self.scrub,
                                              thread=thread)
        self.assertTrue(subscription.subscribed)

    def test_static_page_valid(self):
        StaticPage.objects.create(
                page_id='cryptonomicon',
                page_title='Cryptonomicon',
                content='''
                    “FILIPINOS ARE A WARM, GENTLE, CARING, GIVING people,” Avi
                    says, “which is a good thing since so many of them carry
                    concealed weapons.”
                ''')
        path = reverse('static-page', kwargs={'page_id': 'cryptonomicon'})
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_static_page_invalid(self):
        path = reverse('static-page', kwargs={'page_id': 'dune'})
        response = self.scrub_client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_robots_txt(self):
        forum = Forum(
            name='Garbage Compactor',
            description='Han, Like, Chewbacca, and Leia not included',
            is_trash=True)
        forum.save()
        forum_url = reverse('thread-index', args=(forum.pk,))
        path = reverse('robots')
        response = self.scrub_client.get(path)
        found_trash_rule = False
        
        for row in response.content.split('\n'):
            if row[0] == '#':
                continue

            parts = row.split(': ')
            self.assertEqual(len(parts), 2)

            lh, rh = parts
            self.assertIn(lh, ('User-agent', 'Disallow', 'Allow'))
            found_trash_rule = found_trash_rule or rh == forum_url

        self.assertTrue(found_trash_rule)

class EditPostTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'captcha_period': 0,
        'max_post_chars': 600
    }

    def setUp2(self):
        tutils.create_std_forums()
        self.scrub = tutils.create_user(thread_count=1, post_count=0)
        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)

    def _attempt_edit(self, content, client=None):
        client = client or self.scrub_client

        post = self.scrub.post_set.all()[0]
        path = reverse('edit-post', kwargs={'post_id': post.pk})
        response = client.post(path, {
            'content': content,
            'post': post.pk
        })

        return response

    def test_has_been_edited_default_to_false(self):
        post = self.scrub.post_set.all()[0]
        self.assertEqual(post.postsnapshot_set.all().count(), 0)
        self.assertFalse(post.has_been_edited)

    def test_edit_post(self):
        new_content = 'This post corntains a bad joke'
        self._attempt_edit(new_content)

        post = self.scrub.post_set.all()[0]
        self.assertEqual(new_content, post.content)

    def test_edit_post_too_long(self):
        long_content = '!' * 80000
        self._attempt_edit(long_content)

        post = self.scrub.post_set.all()[0]
        self.assertNotEqual(len(post.content), len(long_content))

    def test_edit_post_generates_snapshot(self):
        post = self.scrub.post_set.all()[0]
        old_content = post.content
        new_content = 'This post corntains a bad joke'

        self._attempt_edit(new_content)

        post = self.scrub.post_set.all()[0]
        self.assertEqual(post.has_been_edited, True)
        self.assertEqual(post.postsnapshot_set.all().count(), 1)

        snapshot = post.postsnapshot_set.all()[0]
        self.assertEqual(snapshot.content, old_content)
        self.assertEqual(snapshot.obsolesced_by, self.scrub)

    def test_non_author_cant_edit(self):
        # URL manipulation is about the extent of his abilities, it's true
        spectral = tutils.create_user(thread_count=0, post_count=0)
        spec_client = Client()
        spec_client.force_login(spectral)

        old_content = self.scrub.post_set.all()[0].content

        resp = self._attempt_edit(
            'use shellcode to reticulate splines',
            spec_client)

        new_content = self.scrub.post_set.all()[0].content

        self.assertEqual(old_content, new_content)

class ThanksViewTestCase(TestCase):
    def setUp(self):
        self.limit = utils.get_config()['initial_account_period_total'] = 3

        tutils.create_std_forums()

        self.thankee = tutils.create_user(thread_count=1, post_count=4)
        self.thanker = tutils.create_user(post_count=4)
        self.noob_thanker = tutils.create_user(post_count=1)

        self.thanker_client = Client()
        self.thanker_client.force_login(self.thanker)

        self.noob_thanker_client = Client()
        self.noob_thanker_client.force_login(self.noob_thanker)


        self.thankee_client = Client()
        self.thankee_client.force_login(self.thankee)

        self.url = reverse('thank-post',
                           args=(self.thankee.post_set.all()[0].pk,))

    def test_happy_path(self):
        resp = self.thanker_client.post(self.url)
        self.assertEqual(self.thankee.thanks_received.count(), 1)

    def test_can_not_thank_set(self):
        resp = self.thankee_client.post(self.url)
        self.assertEqual(self.thankee.thanks_received.count(), 0)

    def test_noobs_cant_thanksforce(self):
        resp = self.noob_thanker_client.post(self.url, {})
        self.assertEqual(self.thankee.thanks_received.count(), 0)

class PostFloodControlTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'initial_account_period_total': 10,
        'initial_account_period_limit': 5
    }

    def setUp2(self):
        tutils.create_std_forums()
        self.scrub = tutils.create_user(thread_count=1, post_count=0)
        self.thread = Thread.objects.get(author=self.scrub)
        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)
        self.path = reverse('new-reply', args=(self.thread.pk,))
        self.limit = utils.get_config('initial_account_period_limit')

    def _attempt_new_post(self):
        prior_count = self.scrub.post_set.count()

        response = self.scrub_client.post(self.path, {
            'content': 'foobar!',
            'thread': self.thread.pk
        })

        return self.scrub.post_set.count() - prior_count

    def test_initial_account_period_compliance(self):
        # Post should be created
        self.assertEqual(self._attempt_new_post(), 1)

    def test_initial_account_period_violation(self):
        tutils.create_posts(self.scrub, self.limit, bulk=True)
        # Post should be rejected
        self.assertEqual(self._attempt_new_post(), 0)

    def test_initial_account_period_violation_cooldown(self):
        tutils.create_posts(self.scrub, self.limit, bulk=True)
        new_created = timezone.now() - utils.get_config(
                'initial_account_period_width')
        self.scrub.post_set.update(created=new_created)

        # Post should be created
        self.assertEqual(self._attempt_new_post(), 1)

    def test_initial_account_period_done(self):
        # Create enough posts to get us out of the initial period
        count = utils.get_config('initial_account_period_total')
        tutils.create_posts(self.scrub, count + 1, bulk=True)

        self.assertEqual(self._attempt_new_post(), 1)

class ThreadActionTestCase(TestCase):
    def setUp(self):
        tutils.create_std_forums()

        self.admin = tutils.create_user()
        self.scrub = tutils.create_user(thread_count=1, post_count=10)

        self.admin.is_admin = True
        self.admin.is_staff = True
        self.admin.save()

        self.thread = Thread.objects.all()[0]

        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)
        self.admin_client = Client()
        self.admin_client.force_login(self.admin)

    def test_non_staff_may_not_delete_posts(self):
        path = reverse('thread-action', kwargs={'thread_id': self.thread.pk})
        response = self.scrub_client.post(path, {'action': 'delete-posts'})
        self.assertEqual(response.status_code, 403)

    def test_staff_may_delete_posts(self):
        path = reverse('thread-action', kwargs={'thread_id': self.thread.pk})
        posts_to_delete = self.thread.post_set.order_by('-created')[8:]

        response = self.admin_client.post(path, {
            'action': 'delete-posts',
            'post': [p.pk for p in posts_to_delete]
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.thread.post_set.count(), 8)

class AdminThreadCreationForum(TestCase):
    def setUp(self):
        tutils.create_std_forums()

        self.admin = tutils.create_user()
        self.scrub = tutils.create_user()

        self.admin.is_admin = True
        self.admin.is_staff = True
        self.admin.save()

        self.admin_client = Client()
        self.admin_client.force_login(self.admin)
        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)

        auth_package = AuthPackage.objects.create(
            logic_package='ADMIN_REQUIRED')

        self.admin_only_forum = Forum.objects.all()[0]
        self.admin_only_forum.create_thread_pack = auth_package
        self.admin_only_forum.save()

        self.limit = utils.get_config()['captcha_period'] = 0

    def test_admin_may_make_thread(self):
        path = reverse('new-thread',
                       kwargs={'forum_id': self.admin_only_forum.pk})
        response = self.admin_client.post(path, {
            'title': 'Presenting: Admin made thread',
            'content': 'by admins, for everyone.',
            'forum': str(self.admin_only_forum.pk)
        })
        self.assertEqual(response.status_code, 302)

    def test_scrub_may_not_make_thread(self):
        path = reverse('new-thread',
                       kwargs={'forum_id': self.admin_only_forum.pk})
        response = self.scrub_client.post(path, {
            'title': 'this shouldn\'t go through',
            'content': 'if you\'re reading this something has gone wrong.',
            'forum': str(self.admin_only_forum.pk)
        })
        self.assertEqual(response.status_code, 403)

class PasswordResetTestCase(TestCase):
    def setUp(self):
        self.franz = tutils.create_user()
        self.franz.email = 'J.K@bank.gov'
        self.franz.save()
        
        self.franz_client = Client()
        self.franz_client.force_login(self.franz)

        self.issue_path = reverse('recovery-initiate')
        self.reset_path = reverse('recovery-reset')

    def tearDown(self):
        mail.outbox = []

    def _update_franz(self):
        self.franz = Poster.objects.get(pk=self.franz.pk)

    def _set_recovery_code(self):
        response = self.franz_client.post(self.issue_path, {
            'username': self.franz.username
        })

    def test_recovery_code_is_initially_null(self):
        self.assertEqual(self.franz.recovery_code, None)

    def test_get_recovery_page(self):
        response = self.franz_client.get(self.issue_path)
        self.assertEqual(response.status_code, 200)

    def test_invalid_email_addr(self):
        response = self.franz_client.post(self.issue_path, {
            'username': 'notarealusername'
        })
        self._update_franz()
        self.assertEqual(self.franz.recovery_code, None)

    def test_initiate(self):
        self._set_recovery_code()
        self._update_franz()
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotEqual(self.franz.recovery_code, None)

    def test_invalid_recovery_get(self):
        self._set_recovery_code()
        response = self.franz_client.get(self.reset_path + '?code=notauuid')
        self.assertEqual(response.status_code, 404)

    def test_valid_recovery_get(self):
        self._set_recovery_code()
        self._update_franz()
        response = self.franz_client.get(
            self.reset_path + '?code=' + self.franz.recovery_code)
        self.assertEqual(response.status_code, 200)

    def test_valid_recovery_post(self):
        self._set_recovery_code()
        self._update_franz()
        old_pass = self.franz.password

        response = self.franz_client.post(
            self.reset_path,
            {
                'password': 'justice',
                'password_repeat': 'justice',
                'code': self.franz.recovery_code
            })

        self._update_franz()
        new_pass = self.franz.password

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(new_pass, old_pass)
        self.assertEqual(self.franz.recovery_code, None)


    def test_invalid_recovery_post(self):
        self._set_recovery_code()
        self._update_franz()
        response = self.franz_client.post(
            self.reset_path,
            {
                'password': 'justice',
                'password_repeat': 'justice',
                'code': 'notauuid'
            })
        self._update_franz()
        self.assertNotEqual(self.franz.recovery_code, None)

    def test_expired_recovery_post(self):
        self._set_recovery_code()
        self._update_franz()
        self.franz.recovery_expiration = (
            timezone.now() - datetime.timedelta(seconds=30))
        self.franz.save()
        response = self.franz_client.post(
            self.reset_path,
            {
                'new_password': 'justice',
                'new_password_repeat': 'justice',
                'code': self.franz.recovery_code
            })
        self.assertEqual(response.status_code, 404)

class AbstractRegistrationTestCase(tutils.ForumConfigTestCase):
    def _register(self,
                  username="Leslie Lamport",
                  email="lamport@softmicro.com",
                  password='TLA Rules'):
        response = self.anon_client.post(
            self.path,
            {
                'username': username,
                'password1': password,
                'password2': password,
                'email': email
            })

        return response

class RegistrationTestCase(AbstractRegistrationTestCase):
    forum_config = {
        'recaptcha_settings': None,
        'enable_registration': True
    }

    def setUp(self):
        tutils.create_std_forums()
        self.anon_client = Client()
        self.path = reverse('register')

    def test_happy_path(self):
        initial_user_count = Poster.objects.count()
        response = self._register() 
        self.assertEqual(Poster.objects.count(), initial_user_count + 1)

    def test_poster_starts_inavtive(self):
        username =  'Leslie Lamport'
        response = self._register() 
        leslie = Poster.objects.get(username=username)
        self.assertFalse(leslie.is_active)

    def test_poster_cant_login(self):
        username = 'Leslie Lamport'
        password = 'BD08081890'
        response = self._register(username=username, password=password) 
        leslie = Poster.objects.get(username=username)

        login_path  = reverse('login')
        client = Client()
        response = client.post(
            login_path, { 'username': username, 'password': password })
        user = auth.get_user(client)

        self.assertFalse(user.is_authenticated)

    def test_email_verification_invalid_code(self):
        path = reverse('verify-email')
        client = Client()
        response = client.get(path, data={'code': 'invalid_code'})
        self.assertEqual(response.status_code, 404)

    def test_email_verification_missing_code(self):
        path = reverse('verify-email')
        client = Client()
        response = client.get(path, data={'kode': 'zork'})
        self.assertEqual(response.status_code, 404)

    def test_email_verification_not_in_db_code(self):
        path = reverse('verify-email')
        client = Client()
        response = client.get(path, data={'code': 'a15d9e9d-caf0-4196-b389-6f4ad5dbcf8d'})
        self.assertEqual(response.status_code, 404)

    def test_email_verification_happy_path(self):
        username =  'Leslie Lamport'
        password = 'Now is when I got my last message'
        response = self._register(username=username, password=password)
        leslie = Poster.objects.get(username=username)

        path = reverse('verify-email')
        client = Client()
        response = client.get(path, data={'code': str(leslie.email_verification_code)})
        self.assertEqual(response.status_code, 200)

        login_path  = reverse('login')
        client = Client()
        response = client.post(login_path,
                               { 'username': username, 'password': password })
        user = auth.get_user(client)
        self.assertEqual(user, leslie)


class EmailNormalizationTestCase(AbstractRegistrationTestCase):
    forum_config = {
        'recaptcha_settings': None,
        'enable_registration': True,
        'email_host_blacklist': ['damnthespam.com']
    }

    def setUp(self):
        tutils.create_std_forums()
        self.anon_client = Client()
        self.client = Client()
        self.path = reverse('register')

    def test_identical_address(self):
        email = "Colin.Maclaurin@gov.scot"
        self._register(username="CM1", email=email)

        user_count = Poster.objects.count()
        self._register(username="CM2", email=email)

        self.assertEqual(Poster.objects.count(), user_count)

    def test_similar_address(self):
        self._register(username="CM1", email= "colinMaclaurin+z@gmail.com")
        user_count = Poster.objects.count()

        self._register(username="CM2", email="Colin.Maclaurin@gmail.com")

        self.assertEqual(Poster.objects.count(), user_count)

    def test_blacklisted_address(self):
        user_count = Poster.objects.count()
        self._register(username="I.N.", email= "isaac.newton@damnthespam.com")
        self.assertEqual(Poster.objects.count(), user_count)

    def test_diff_addres(self):
        self._register(username="CM1", email= "Colin.Maclaurin@gov.scot")
        user_count = Poster.objects.count()
        self._register(username="CM2", email= "Maclaurin.Colin@gov.scot")
        self.assertEqual(Poster.objects.count(), user_count + 1)

class RegistrationDisabledTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'recaptcha_settings': None,
        'enable_registration': False
    }

    def setUp2(self):
        tutils.create_std_forums()
        self.anon_client = Client()
        self.path = reverse('register')

    def test_only_path(self):
        initial_user_count = Poster.objects.count()

        response = self.anon_client.post(
            self.path,
            {
                'username': 'Groucho Marx',
                'password1': 'BD08081890',
                'password2': 'BD08081890',
                'email': 'gmarx@contrarian.club'
            })

        self.assertEqual(Poster.objects.count(), initial_user_count)

class RegistrationByInviteTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'recaptcha_settings': None,
        'captcha_period': 0,
        'enable_registration': False,
        'enable_invites': True
    }

    def setUp2(self):
        tutils.create_std_forums()

        self.admin = tutils.create_user()
        self.anon_client = Client()

        self.reg_code = RegistrationCode()
        self.reg_code.generated_by = self.admin
        self.reg_code.save()

        self.path = reverse('register-with-code')

    def test_happy_path(self):
        response = self.anon_client.post(
            self.path,
            {
                'username': 'Groucho Marx',
                'password1': 'BD08081890',
                'password2': 'BD08081890',
                'email': 'gmarx@contrarian.club',
                'registration_code': self.reg_code.code
            })

        self.assertEqual(Poster.objects.count(), 2)

        self.reg_code = tutils.refresh_model(self.reg_code)
        self.assertFalse(self.reg_code.used_by == None)

    def test_unhappy_path(self):
        response = self.anon_client.post(
            self.path,
            {
                'username': 'Groucho Marx',
                'password1': 'BD08081890',
                'password2': 'BD08081890',
                'email': 'gmarx@contrarian.club',
                'registration_code': 'not_a_valid_code'
            })

        self.assertEqual(Poster.objects.count(), 1)
        self.assertTrue('registration_code' in response.context['form'].errors)

    def test_double_use(self):
        response = self.anon_client.post(
            self.path,
            {
                'username': 'Groucho Marx',
                'password1': 'BD08081890',
                'password2': 'BD08081890',
                'email': 'gmarx@contrarian.club',
                'registration_code': self.reg_code.code
            })

        self.assertEqual(Poster.objects.count(), 2)

        self.reg_code = tutils.refresh_model(self.reg_code)
        self.assertFalse(self.reg_code.used_by == None)

        # Now log out and try to re-register
        self.anon_client.logout()

        response = self.anon_client.post(
            self.path,
            {
                'username': 'Groucho Marx II',
                'password1': 'BD08081890',
                'password2': 'BD08081890',
                'email': 'gmarx2@contrarian.club',
                'registration_code': self.reg_code.code
            })

        self.assertEqual(Poster.objects.count(), 2)
        self.assertTrue('registration_code' in response.context['form'].errors)

    def test_expiration(self):
        self.reg_code.expires = timezone.now() - datetime.timedelta(seconds=30)
        self.reg_code.save()

        response = self.anon_client.post(
            self.path,
            {
                'username': 'Groucho Marx',
                'password1': 'BD08081890',
                'password2': 'BD08081890',
                'email': 'gmarx@contrarian.club',
                'registration_code': self.reg_code.code
            })

        self.assertEqual(Poster.objects.count(), 1)
        self.assertTrue('registration_code' in response.context['form'].errors)

class GenerateInviteCodeTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'enable_registration': False,
        'enable_invites': True
    }

    def setUp(self):
        super(GenerateInviteCodeTestCase, self).setUp()
        self.don = tutils.create_user()
        self.scrub = tutils.create_user()

        self.don_client = Client()
        self.don_client.force_login(self.don)

        self.scrub_client = Client()
        self.scrub_client.force_login(self.scrub)

        AccessControlGroup.get_acg('INVITORS').members.add(self.don)

        self.path = reverse('generate-invite')

    def test_scrub_cant_invite(self):
        res1 = self.scrub_client.get(self.path)
        res2 = self.scrub_client.post(self.path, {})

        self.assertEqual(res1.status_code, 403)
        self.assertEqual(res2.status_code, 403)

    def test_donny_can_invite_get(self):
        res = self.don_client.get(self.path)
        self.assertEqual(res.status_code, 200)

    def test_donny_can_invite_post(self):
        res = self.don_client.post(self.path, {})
        self.assertEqual(res.status_code, 302)

        reg_code = RegistrationCode.objects.order_by('-generated_on')[0]
        self.assertEqual(self.don.pk, reg_code.generated_by.pk)
        self.assertEqual(reg_code.used_by, None)
        self.assertEqual(reg_code.used_on, None)

 
class LoginTestCase(TestCase):
    def setUp(self):
        self.password = '私わ大津展之です'
        self.path = reverse('login')

        self.otsu = tutils.create_user()
        self.otsu.set_password(self.password)
        self.otsu.save()

        self.otsu_client = Client()

    def test_correct_unicode_password(self):
        response = self.otsu_client.post(
            self.path,
            {
                'username': self.otsu.username,
                'password': self.password,
            })

        user = auth.get_user(self.otsu_client)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.pk, self.otsu.pk)
        
    def test_incorrect_unicode_password_success(self):
        response = self.otsu_client.post(
            self.path,
            {
                'username': self.otsu.username,
                'password': self.password[:-1],
            })

        user = auth.get_user(self.otsu_client)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(user.is_authenticated)

class UserCPTestCase(tutils.ForumConfigTestCase):
    forum_config = {'captcha_period': 0}

    def setUp2(self):
        tutils.create_std_forums()

        self.don = tutils.create_user(thread_count=1, post_count=1)
        self.fran = tutils.create_user(thread_count=0, post_count=0)

        self.thread = Thread.objects.all()[0]
        self.thread.subscribe(self.don)

        self.thread.mark_read(self.don, self.thread.get_last_post())

        self.don_client = Client()
        self.don_client.force_login(self.don)


    def test_mark_all_read(self):
        ucp_path = reverse('usercp')
        mar_path = reverse('read-subscriptions')

        # Don starts with no new items in his new subs list
        response = self.don_client.get(ucp_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['threads']), 0)

        # Bump his subscribed thread
        tutils.create_post(self.fran, self.thread)

        # Make sure he now has a new sub thread
        response = self.don_client.get(ucp_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['threads']), 1)

        # Mark all threads as read
        response = self.don_client.post(mar_path)
        self.assertEqual(response.status_code, 302)

        # Verify Don has no more new sub'd threads
        response = self.don_client.get(ucp_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['threads']), 0)

        # Bump again
        tutils.create_post(self.fran, self.thread)

        # Make sure Don sees the thread as bumped
        response = self.don_client.get(ucp_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['threads']), 1)

class ReportPostTestCase(tutils.ForumConfigTestCase):
    forum_config = {
        'recaptcha_settings': None,
        'report_reasons': (('TOO_PRETTY', 'Too pretty'),),
    }

    def setUp(self):
        tutils.create_std_forums()

        self.don = tutils.create_user(thread_count=1, post_count=1)
        self.fran = tutils.create_user(thread_count=0, post_count=0)
        self.lanny = tutils.create_user(thread_count=0, post_count=0)

        self.lanny.is_staff = True
        self.lanny.is_admin = True
        self.lanny.save()

        self.don_post = self.don.post_set.all()[0]

        self.fran_client = Client()
        self.fran_client.force_login(self.fran)


    def _report_post(self, post):
        path = reverse('report-post', args=(post.pk,))
        return self.fran_client.post(path, {
            'post': post.pk,
            'reason': 'TOO_PRETTY',
            'explanation': ('Post was made by a user who is too pretty '
                            'and that offends me.')}
        )

    def test_happy_path_report(self):
        pm_count = PrivateMessage.objects.count()
        response = self._report_post(self.don_post)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PrivateMessage.objects.count(), pm_count + 2)


    def test_extra_long_username_report(self):
        pm_count = PrivateMessage.objects.count()

        max_len = Poster._meta.get_field('username').max_length
        username = 'I\'m a pretty princess'
        username = username + ('!' * (max_len - len(username)))

        fin = tutils.create_user(post_count=1, username=username)
        post = fin.post_set.all()[0]
        response = self._report_post(post)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PrivateMessage.objects.count(), pm_count + 2)
