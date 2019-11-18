import urllib.parse
import urllib.request, urllib.parse, urllib.error

from django import template

register = template.Library()

def unfuck_percent_encoded_utf8(fucked_unicode_str):
    # OK So... *dramatic pause*
    # (((Some))) browsers insist on transforming unicode characters outside of
    # the ASCII range to their UTF-8 encoding, and then url encoding that byte
    # sequence. If you want my opinion this is harmful because it's a big pain
    # in my ass necessitating this code when it would be perfectly reasonable
    # to just send UTF-8 byte sequences in URLs but fuck it, until Google/Apple
    # /Mozilla start considering overly long comments in obscure codebases as
    # standards this code is gonna have to stick around.
    #
    # To compound this issue, python's urlparse.parse_qs has the highly
    # questionable behavior of treating every percent encoded octet at a
    # seperate codepoint which is like the opposite how the major browser
    # vendors have decided to do it. Theoretically this should be fine if
    # browsers did The Right Thing but given the reality of the situation it's
    # imprudent and requires me to fix this situation here with the jank that
    # follows.
    #
    # So what do we do about it? Instead of trying to monkey patch urlparse or
    # something we instead consult the (incorrect) values that it returns. We
    # construct a byte string. For each codepoint in the input string we either
    #
    #  A) insert a byte into our byte string iff the codepoint is less than
    #     2^8 or...
    #  B) insert a byte sequence into the byte string corrosponding to the utf-8
    #     encoded value for that codepoint.
    #
    # This bytestring should now be correctly encoded UTF-8, caller can decode
    # if  they want
    # 
    # Browsers doing The Right Thing with high codepoints are covered under B,
    # normal ascii range characters are covered under A, and fucked utf-8 then
    # percent encoded strings are also covered under A.
    #
    # This also has the benefit that if someone really decides to be an ass and
    # sends a url where there is both "raw" UTF-8 encoded codepoints and percent
    # encoded UTF-8 encoded sequences the url will somehow correctly get
    # handled.
    #
    # This is probably pretty slow but I'm fairly confident it's correct.

    if isinstance(fucked_unicode_str, str):
        return ''.join([(chr(ord(c)) if ord(c) < 256 else c.encode('utf-8')) for c in fucked_unicode_str])
    else:
        return str(fucked_unicode_str)

RANGE_WIDTH = 3
@register.simple_tag
def nice_page_set(page):
    pages = []
    pages.extend(list(range(1, RANGE_WIDTH+1)))
    pages.extend(list(range(page.paginator.num_pages-RANGE_WIDTH,
                       page.paginator.num_pages+1)))
    pages.extend(list(range(page.number-RANGE_WIDTH, page.number+RANGE_WIDTH)))

    pages = [n for n in pages if n <= page.paginator.num_pages and n > 0]
    pages = list(set(pages))
    pages.sort()

    elip_pages = []
    for idx, n in enumerate(pages):
        if idx != 0 and n != pages[idx-1] + 1:
            elip_pages.append(-1)

        elip_pages.append(n)

    return elip_pages

@register.filter
def mixin_page_param(base_url, page_number):
    parsed_url = urllib.parse.urlparse(base_url)
    query = urllib.parse.parse_qs(parsed_url.query)
    query['p'] = [page_number]

    one_pairs = []
    for key, values in list(query.items()):
        for value in values:
            one_pairs.append((
                unfuck_percent_encoded_utf8(key),
                unfuck_percent_encoded_utf8(value)))

    qs = urllib.parse.urlencode(one_pairs)
    url_dict = parsed_url._asdict()
    url_dict['query'] = qs
    
    return urllib.parse.urlunparse(urllib.parse.ParseResult(**url_dict))
