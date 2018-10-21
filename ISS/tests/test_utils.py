# -*- coding: utf-8 -*-

from datetime import timedelta

from ISS import utils
import tutils

SIGNED_MESSAGE = """
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

[quote author="Don Knuth"]
The whole thing that makes a mathematician’s life worthwhile is that he gets the grudging admiration of three or four colleagues.
[/quote]

The mathematician in question had received just a bit more admiration than that.
-----BEGIN PGP SIGNATURE-----

iQJOBAEBCAA4FiEEaplk9V8kovCcp8BrznljHEc+lFoFAlvL0UwaHGxhbi5yb2dl
cnMuYm9va0BnbWFpbC5jb20ACgkQznljHEc+lFo8+A/8Cl4abu6AgurIJcyrXS2x
YqRAZSwQHG5KzwF5pbqRjr5EDILL8+DBlPXLlKgFVghiHTk3YSTZNF03igNEqC5Q
jiDvmMH6LkdE3a27CWdgT8/to8HNBEoWAOAVfT+UqA830+CbKKLJXX/N40I+YyZx
nSsKc88AwD1B5ZA3PP4pz6qq2euSLsk6F/UwL02Z9vn+Z14LCmzC/bn6sYZue7cy
sXA94rJp/d7ji5aHffQNT2Acb4xkToiwJ3DAIxjIv6D508hFU2ZTFVvZ2t5glge1
49nKrq2Ps8cY+u6b6K2IFuo9C//ufQ5wbti7VX1WodEOIcJTugsj5CBSJ6mNE5Zk
SXKHqoT+UQZqmuHIsC9FmRaNROhljGX+AncOUh6XIHS3hlJ3xieahB+vFvJEj8wF
CdZ6hiuLS1aS4Pyy+5sOUiZ1l6Z38/w1O4w+Fjx6TQmv9pmHU/HH4Il2w6f7CkvN
PwCC0RGoSV6pJTowj+5iMfg83q7/kQQKHSbdNpUvVJbzysE+qmux+3jf1X/DT4ol
DUCueBuXwvwf9i04VCxdiQmpvhZcLBphwtxCHaTizi0/v0JPJnmFV71HMAAO5l54
OrSX+wqPM04tvOQXFXI1XsBUbiePoERLVLwf3Ot+i/viXAXU9fJlp6SMQb9y7Cjg
zod/w6ycFro2AsLQaHVZwqw=
=tKYo
-----END PGP SIGNATURE-----
"""

class UtilsTestCase(tutils.ForumConfigTestCase):
    cannonical_form_tests = (
        ('42s', timedelta(seconds=42)),
        ('1w', timedelta(days=7)),
        ('1y 2d', timedelta(days=358)),
        ('2w 42s', timedelta(days=14, seconds=42)),
        ('2y 2d 2h 2m 2s', timedelta(
            seconds=(((356*2 + 2)*24 + 2) * 60 + 2) * 60 + 2))
    )

    strange_tests = (
        ('120s', timedelta(seconds=120)),
        ('48h', timedelta(days=2))
    )

    def setUp2(self):
        self.cparser = utils.get_closure_bbc_parser()

    def test_cannonical_parse_duration(self):
        for (rep, val) in self.cannonical_form_tests:
            exp = val.total_seconds()
            act = utils.parse_duration(rep).total_seconds()

            msg = 'Expected "%s" to evaluate to %d seconds, got %d.' %  (
                rep, exp, act)

            self.assertEqual(exp, act, msg)

    def test_strange_parse_duration(self):
        for (rep, val) in self.strange_tests:
            exp = val.total_seconds()
            act = utils.parse_duration(rep).total_seconds()

            msg = 'Expected "%s" to evaluate to %d seconds, got %d.' %  (
                rep, exp, act)

            self.assertEqual(exp, act, msg)

    def test_format_duration(self):
        for (rep, val) in self.cannonical_form_tests:
            act = utils.format_duration(val)
            msg = 'Expected %r to format to %r, got %r' %  (val, rep, act)
            self.assertEqual(rep, act, msg)

    def test_parse_format_parse(self):
        for (rep, val) in self.cannonical_form_tests:
            exp = val.total_seconds()
            act = utils.parse_duration(
                utils.format_duration(
                    utils.parse_duration(rep))
                ).total_seconds()


            self.assertEqual(exp, act)

    def test_closure_quote_denesting(self):
        bbcontent = """
            [quote]
            Beware of bugs in the above code; I have only proved it correct, not
            tried it.
            [/quote]

            Lord have mercy on our souls.
        """
        denested = self.cparser.format(bbcontent)
        self.assertEqual(denested.strip(), 'Lord have mercy on our souls.')

    def test_closure_cool_tag_removal(self):
        bbcontent = ('What\'s [byusingthistagIaffirmlannyissupercool]up'
                     '[/byusingthistagIaffirmlannyissupercool] with it.')
        decooled = self.cparser.format(bbcontent)
        self.assertEqual(decooled, 'What\'s up with it.')

    def test_closure_PGP_removal(self):
        depgpd = self.cparser.format(SIGNED_MESSAGE)
        self.assertEqual(depgpd.strip(), 'The mathematician in question '
                'had received just a bit more admiration than that.')

