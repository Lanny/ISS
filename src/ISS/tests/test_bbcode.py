# -*- coding: utf-8 -*-
import re

import ISS.iss_bbcode
from ISS.iss_bbcode import build_parser

from . import tutils

def slw(s):
    """
    Strip leading whitespace.
    """
    return re.sub(s, r'^ +', '')


class VideoTestCase(tutils.ForumConfigTestCase):
    def test_valid_bitchute_embed(self):
        parser = build_parser(('VIDEO',))
        bbc = '[video]https://www.bitchute.com/video/8cHD9kgLTCzq/[/video]'
        expected = (
            '<iframe width="640" height="480" class="yt-embed" '
            'src="https://www.bitchute.com/embed/8cHD9kgLTCzq" frameborder="0"'
            ' allowfullscreen></iframe>'
        )
        actual = parser.format(bbc)
        self.assertEqual(expected, actual)

    def test_simple_video_XSS(self):
        parser = build_parser(('VIDEO',))
        bbc = '[video]javascript:alert("haiiii")[/video]'
        expected = '[video]javascript:alert(&quot;haiiii&quot;)[/video]'
        actual = parser.format(bbc)
        self.assertEqual(expected, actual)

    def test_slightly_trickier_XSS(self):
        parser = build_parser(('VIDEO',))
        bbc = '[video]javascript:(alert("haiiii"), {}).mp4[/video]'
        expected = '[video]javascript:(alert(&quot;haiiii&quot;), {}).mp4[/video]'
        actual = parser.format(bbc)
        self.assertEqual(expected, actual)

    def test_valid_long_yt_embed(self):
        parser = build_parser(('VIDEO',))
        bbc = '[video]https://www.youtube.com/watch?v=6DaL-Z4dwzI[/video]'
        expected = '<iframe width="640" height="480" class="yt-embed" src="https://www.youtube.com/embed/6DaL-Z4dwzI?start=0" frameborder="0" allowfullscreen></iframe>'
        actual = parser.format(bbc)
        self.assertEqual(expected, actual)
        
    def test_invalid_long_yt_embed(self):
        parser = build_parser(('VIDEO',))
        bbc = '[video]https://kkk.youtube.com/watch?v=6DaL-Z4dwzI[/video]'
        actual = parser.format(bbc)
        self.assertEqual(bbc, actual)

    def test_non_video_yt_embed(self):
        parser = build_parser(('VIDEO',))
        bbc = '[video]https://www.youtube.com/account[/video]'
        actual = parser.format(bbc)
        self.assertEqual(bbc, actual)
        
class QuoteTestCase(tutils.ForumConfigTestCase):
    def test_no_attrib_quote(self):
        parser = build_parser(('QUOTE',))
        bbc = '[quote]foo bar[/quote]'
        actual = parser.format(bbc)
        expected = '<blockquote>foo bar</blockquote>'
        self.assertEqual(expected, actual)

    def test_author_only_attrib_quote(self):
        parser = build_parser(('QUOTE',))
        bbc = '[quote author="D-Dawg"]Dogs and philosophers to the most good and receive the least praise[/quote]'
        actual = parser.format(bbc)
        expected = '<blockquote>\n<small class="attribution">Originally posted by D-Dawg</small>\nfoo bar\n</blockquote>'
        self.assertEqual(slw(expected), slw(actual))
