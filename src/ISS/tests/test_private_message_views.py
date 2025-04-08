# -*- coding: utf-8 -*-

from django.test import Client
from django.urls import reverse

from ISS.models import PrivateMessage
from . import tutils


class PrivateMessageViewsTestCase(tutils.ForumConfigTestCase):
    forum_config = {'captcha_period': 0}

    def setUp(self):
        tutils.create_std_forums()

        self.kurt = tutils.create_user()
        self.bertrand = tutils.create_user()

        self.kurt_client = Client()
        self.kurt_client.force_login(self.kurt)

        self.bertrand_client = Client()
        self.bertrand_client.force_login(self.bertrand)

    def test_pms_show_up_in_inbox(self):
        tutils.send_pm(self.kurt, [self.bertrand])
        tutils.send_pm(self.kurt, [self.bertrand])
        tutils.send_pm(self.kurt, [self.bertrand])

        path = reverse('inbox')
        response = self.bertrand_client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page']), 3)

    def test_reading_inboxed_pm_makes_read(self):
        sent, kept = tutils.send_pm(self.kurt, [self.bertrand])
        sent_pm = sent[0]
        self.assertFalse(sent_pm.read)

        path = reverse('read-pm', kwargs={'pm_id': sent_pm.pk})
        response = self.bertrand_client.get(path)

        self.assertEqual(response.status_code, 200)
        sent_pm = PrivateMessage.objects.get(pk=sent_pm.pk)
        self.assertTrue(sent_pm.read)

    def test_can_read_sent_pm(self):
        sent, kept = tutils.send_pm(self.kurt, [self.bertrand])
        kept_pm = kept[0]

        path = reverse('read-pm', kwargs={'pm_id': kept_pm.pk})
        response = self.kurt_client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_cant_read_someone_elses_pm(self):
        sent, kept = tutils.send_pm(self.kurt, [self.bertrand])
        sent_pm = sent[0]

        path = reverse('read-pm', kwargs={'pm_id': sent_pm.pk})
        response = self.kurt_client.get(path)
        self.assertEqual(response.status_code, 403)

    def test_mak_all_as_read(self):
        (sent_1,), _ = tutils.send_pm(self.kurt, [self.bertrand])
        (sent_2,), _ = tutils.send_pm(self.kurt, [self.bertrand])
        (sent_3,), _ = tutils.send_pm(self.bertrand, [self.kurt])

        sent_1.read = True
        sent_1.save()

        path = reverse('pms-action')
        response = self.bertrand_client.post(path, {
            'action': 'mark-all-read'
        })
        self.assertEqual(response.status_code, 302)

        self.assertTrue(PrivateMessage.objects.get(pk=sent_1.pk).read)
        self.assertTrue(PrivateMessage.objects.get(pk=sent_2.pk).read)

        # Bertrand's action shouldn't impact Kurt's PMs
        self.assertFalse(PrivateMessage.objects.get(pk=sent_3.pk).read)
