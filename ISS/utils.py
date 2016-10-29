import bbcode

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator, Page
from django.conf import settings

config_defaults = {
    'forum_name': 'INTERNATIONAL SPACE STATION',
    'banner_dir': 'banners',
    'min_post_chars': 1,
    'min_thread_title_chars': 1,
    'threads_per_forum_page': 20,
    'posts_per_thread_page': 20,
    'general_items_per_page': 20
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

    def render_quote(tag_name, value, options, parent, context):
        author = options.get('author', None)

        if author:
            template = """
                <blockquote>
                  <small class="attribution">Originally posted by %s</small>
                  %s
                </blockquote>
            """

            return template % (author, value)

        else:
            return '<blockquote>%s</blockquote>' % value

    parser.add_formatter('quote',
                         render_quote,
                         strip=True,
                         swallow_trailing_newline=True)
        

    return parser

class ThreadFascet(object):
    """
    Fusion a thread and a request, representing that thread as perceived by the
    requesting user. Behaves like a Thread object, from the template's
    perspective in all but a few instances where rendering id contengent on the
    user.
    """
    def __init__(self, thread, request):
        self._thread = thread
        self._request = request

    def __getitem__(self, field):
        prop = getattr(self._thread, field)

        if field in ('has_unread_posts',):
            if not self._request.user.is_authenticated():
                return True

            return prop(self._request.user)

        elif callable(prop):
            return prop()
        else:
            return prop

class MappingPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        super(MappingPaginator, self).__init__(*args, **kwargs)

        self._map_function = lambda x: x

    def install_map_func(self, f):
        self._map_function = f

    def _get_page(self, object_list, number, paginator):
        object_list = map(self._map_function, object_list)

        return Page(object_list, number, paginator)
