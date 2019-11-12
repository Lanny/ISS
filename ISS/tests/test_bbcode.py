# -*- coding: utf-8 -*-

from ISS.iss_bbcode import build_parser

import tutils

class BBCodeTestCase(tutils.ForumConfigTestCase):
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
