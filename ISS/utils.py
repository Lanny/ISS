import bbcode
import urlparse
import re

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator, Page
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

config_defaults = {
    'forum_name': 'INTERNATIONAL SPACE STATION',
    'banner_dir': 'banners',
    'min_post_chars': 1,
    'min_thread_title_chars': 1,
    'threads_per_forum_page': 20,
    'posts_per_thread_page': 20,
    'general_items_per_page': 20,
    'ninja_edit_grace_time': 120
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

def render_mixed_mode(request, templates, additional={}):
    data = {}

    for key_name, template, ctx in templates:
        markup = render(request, template, ctx).content
        data[key_name] = markup

    data.update(additional)

    return JsonResponse(data)
    
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

    def render_video(tag_name, value, options, parent, context):
        url = urlparse.urlparse(value)

        embed_pattern = ('<iframe width="640" height="480" '
            'src="https://www.youtube.com/embed/%s?start=%s" frameborder="0" '
            'allowfullscreen></iframe>')

        if url.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            query = urlparse.parse_qs(url.query, keep_blank_values=False)

            if 'v' not in query:
                return '[video]%s[/video]' % value

            v = query['v'][0]

            if not re.match('[\-0-9a-zA-Z]+', v):
                return '[video]%s[/video]' % value

            return embed_pattern % (v, '0')

        elif url.netloc in ('youtu.be',):
            query = urlparse.parse_qs(url.query, keep_blank_values=False)
            stripped_path = url.path[1:]
            t = query.get('t', ['0'])[0]

            if not re.match('[\-0-9a-zA-Z]+', stripped_path):
                return '[video]%s[/video]' % value
            if t and not re.match(r'\d+', t):
                return '[video]%s[/video]' % value

            return embed_pattern % (stripped_path, t)

        else:
            return '[video]%s[/video]' % value

    parser.add_formatter('video', render_video)



    default_url_hanlder, _ = parser.recognized_tags['url']
    parser.add_formatter('link', default_url_hanlder, replace_cosmetic=False)
        
    return parser

def get_closure_bbc_parser():
    c_parser = bbcode.Parser(
        newline='\n', install_defaults=False, escape_html=False,
        replace_links=False, replace_cosmetic=False)

    def depyramiding_quote_render(tag_name, value, options, parent, context):
        if tag_name == 'quote':
            return ''

        return value

    c_parser.add_formatter('quote', depyramiding_quote_render)

    return c_parser


class ThreadFascet(object):
    """
    Fusion a thread and a request, representing that thread as perceived by the
    requesting user. Behaves like a Thread object, from the template's
    perspective in all but a few instances where rendering is contengent on the
    user.
    """
    def __init__(self, thread, request):
        self._thread = thread
        self._request = request

    def __getitem__(self, field):
        prop = getattr(self._thread, field)

        if field in ('has_unread_posts', 'get_jump_post'):
            return prop(self._request.user)

        elif callable(prop):
            return prop()
        else:
            return prop

class ForumFascet(object):
    """
    Same as above, but for forums.
    """
    def __init__(self, forum, request):
        self._forum = forum
        self._request = request

    def __getitem__(self, field):
        prop = getattr(self._forum, field)

        if field in ('is_unread',):
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
