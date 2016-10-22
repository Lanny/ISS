import bbcode

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.conf import settings

config_defaults = {
    'forum_name': 'INTERNATIONAL SPACE STATION',
    'banner_dir': 'banners',
    'min_post_chars': 1,
    'min_thread_title_chars': 1
}

config = config_defaults.copy()
config.update(settings.FORUM_CONFIG)


def get_config(key=None):
    if not key:
        return config
    else:
        return config_defaults.get(key)

def page_by_request(paginator, request):
    page_num = request.GET.get('p')

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page
    
def get_standard_bbc_parser(embed_images=True, escape_html=True):
    parser = bbcode.Parser(escape_html=escape_html, replace_links=False)

    if embed_images:
        parser.add_simple_formatter(
            'img',
            '<a class="img-embed" href="%(value)s"><img src="%(value)s"></a>')
    else:
        parser.add_simple_formatter(
            'img',
            '<a class="img-link" href="%(value)s">embedded image</a>')

    return parser
