import urlparse
import urllib

from django import template

register = template.Library()

RANGE_WIDTH = 3
@register.assignment_tag
def nice_page_set(page):
    pages = []
    pages.extend(range(1, RANGE_WIDTH+1))
    pages.extend(range(page.paginator.num_pages-RANGE_WIDTH,
                       page.paginator.num_pages+1))
    pages.extend(range(page.number-RANGE_WIDTH, page.number+RANGE_WIDTH))

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
    parsed_url = urlparse.urlparse(base_url)
    query = urlparse.parse_qs(parsed_url.query)
    query['p'] = [page_number]

    one_pairs = []
    for key, values in query.items():
        for value in values:
            one_pairs.append((key.encode('utf-8'), value.encode('utf-8')))

    qs = urllib.urlencode(one_pairs)
    url_dict = parsed_url._asdict()
    url_dict['query'] = qs

    return urlparse.urlunparse(urlparse.ParseResult(**url_dict))
