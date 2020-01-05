# -*- coding: utf-8 -*-
import re

from ISS.templatetags import pagination

from . import tutils

class PaginationTestCase(tutils.ForumConfigTestCase):
    def test_mixin_page_param(self):
        cases = (
            ('/foo/bar', 7, '/foo/bar?p=7'),
            ('/foo/bar?baz=42', 7, '/foo/bar?baz=42&p=7'),
            (
                '/search?q=onion&search_type=posts&author=Sophi%D0%B5',
                42,
                '/search?q=onion&search_type=posts&author=Sophi%D0%B5&p=42'
            ),
            (
                '/search?q=onion&search_type=posts&author=Sophi\u0435',
                42,
                '/search?q=onion&search_type=posts&author=Sophi%D0%B5&p=42'
            ),
        )

        for base, page_num, expected in cases:
            url = pagination.mixin_page_param(base, page_num)
            self.assertEqual(url, expected)
