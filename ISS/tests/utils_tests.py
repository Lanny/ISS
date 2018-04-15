# -*- coding: utf-8 -*-

from datetime import timedelta

from ISS import utils
import test_utils

class UtilsTestCase(test_utils.ForumConfigTestCase):
    tests = (
        ('42s', timedelta(seconds=42)),
        ('1y 2d', timedelta(days=358)),
        ('2w 42s', timedelta(days=14, seconds=42)),
        ('2y 2d 2h 2m 2s', timedelta(
            seconds=(((356*2 + 2)*24 + 2) * 60 + 2) * 60 + 2)),
        ('120s', timedelta(seconds=120)),
        ('48h', timedelta(days=2))
    )

    def test_parse_duration(self):
        for (rep, val) in self.tests:
            exp = val.total_seconds()
            act = utils.parse_duration(rep).total_seconds()

            msg = 'Expected "%s" to evaluate to %d seconds, got %d.' %  (
                rep, exp, act)

            self.assertEqual(exp, act, msg)


