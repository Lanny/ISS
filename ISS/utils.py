import bbcode
import urlparse
import urllib2
import re

from lxml import etree

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator, Page
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render

from ISS.models import *

DO_NOT_LINK_TAGS = { 'video', 'pre' }

config_defaults = {
    'forum_name': 'INTERNATIONAL SPACE STATION',
    'banner_dir': 'banners',
    'min_post_chars': 1,
    'max_post_chars': 19475, # No. characters in the first chapter of Dune
    'min_thread_title_chars': 1,
    'threads_per_forum_page': 20,
    'posts_per_thread_page': 20,
    'general_items_per_page': 20,
    'ninja_edit_grace_time': 120,
    'private_message_flood_control': 30,
    'title_ladder': (
        (100, 'Regular'),
        (10, 'Acolyte'),
        (0, 'Novice')
    ),
    'recaptcha_settings': None,
    'max_avatar_size': 128*1024,
    'junk_user_username': 'The Self Taught Man',
    'system_user_username': 'Wintermute',
    'report_message': 'Select a reason for reporting this post:',
    'report_reasons': (
        ('SPAM_BOT', 'Spam bot/spamming script'),
        ('ILLEGAL_CONTENT', 'Illegal content'),
        ('INTENTIONAL_DISRUPTION', 'Intentional disruption')
    ),
    'control_links': (
        ('RLINK', 'Subscriptions', 'usercp', 'is_authenticated', None),
        ('RLINK', 'Latest Threads', 'latest-threads', 'always', None),
        ('PMS', 'Inbox', 'inbox', 'is_authenticated', None),
        ('RLINK', 'Search', 'search', 'always', None),
        ('RLINK', 'Admin', 'admin:index', 'is_admin', None),
        ('FORM', 'Logout', 'logout', 'is_authenticated', None),
        ('RLINK', 'Register', 'register', 'is_not_authenticated', None),
    ),
    'static_pages': ()
}

config = config_defaults.copy()
config.update(settings.FORUM_CONFIG)
config['title_ladder'] = sorted(config['title_ladder'], key=lambda x: x[0],
                                reverse=True)

class MethodSplitView(object):
    def __call__(self, request, *args, **kwargs):
        if getattr(self, 'active_required', False):
            if not request.user.is_active:
                raise HttpResponseForbidden('You must be an active user '
                                            'to do this')
        if getattr(self, 'staff_required', False):
            if not request.user.is_staff:
                raise HttpResponseForbidden('You must be staff to do this.')

        meth = getattr(self, request.method, None)

        if not meth:
            return HttpResponseBadRequest('Request method %s not supported'
                                          % request.method)
        
        return meth(request, *args, **kwargs)

    @classmethod
    def as_view(cls):
        if getattr(cls, 'require_login', False):
            return login_required(cls())
        else:
            return cls()

def get_config(key=None):
    if not key:
        return config
    else:
        return config.get(key)

def page_by_request(paginator, request):
    page_num = request.GET.get('p')

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page

def get_posts_per_page(poster):
    if poster.is_authenticated():
        return poster.posts_per_page
    else:
        return get_config('posts_per_thread_page')

def get_posts_page(qs, request):
    posts_per_page = get_posts_per_page(request.user)
    paginator = Paginator(qs, posts_per_page)
    page = page_by_request(paginator, request)

    return page

def render_mixed_mode(request, templates, additional={}):
    data = {}

    for key_name, template, ctx in templates:
        markup = render(request, template, ctx).content
        data[key_name] = markup

    data.update(additional)

    return JsonResponse(data)

class EmbeddingNotSupportedException(Exception):
    pass

def _video_markup_for_url(urlstr):
    """
    Given a link to an embedable video, returns markup to embed that video in
    a page. If the link it malformed or to an unknown video hosting service
    throws EmbeddingNotSupportedException.
    """
    url = urlparse.urlparse(urlstr)

    embed_pattern = ('<iframe width="640" height="480" '
        'src="https://www.youtube.com/embed/%s?start=%s" frameborder="0" '
        'allowfullscreen></iframe>')

    if url.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        query = urlparse.parse_qs(url.query, keep_blank_values=False)

        if 'v' not in query:
            raise EmbeddingNotSupportedException('No video ID provided.')

        v = query['v'][0]

        if not re.match('[\-_0-9a-zA-Z]+', v):
            raise EmbeddingNotSupportedException('Bad video ID.')

        return embed_pattern % (v, '0')

    elif url.netloc in ('youtu.be',):
        query = urlparse.parse_qs(url.query, keep_blank_values=False)
        stripped_path = url.path[1:]
        t = query.get('t', ['0'])[0]

        if not re.match('[\-_0-9a-zA-Z]+', stripped_path):
            raise EmbeddingNotSupportedException('Bad video ID.')
        if t and not re.match(r'\d+', t):
            raise EmbeddingNotSupportedException('Bad time stamp.')

        return embed_pattern % (stripped_path, t)

    else:
        raise EmbeddingNotSupportedException('Unrecognized service.')


def bandcamp_markup_for_url(urlstr):
    url = urlparse.urlparse(urlstr)

    parser = etree.HTMLParser(no_network=False)
    req = urllib2.urlopen(urlstr)
    tree = etree.parse(req, parser)
    embed_meta = tree.xpath('//meta[@property="og:video:secure_url"]')
    embed_url = embed_meta[0].get('content')

    markup = ('<iframe class="bandcamp-embed" '
        + 'src="%s" ' % embed_url
        + 'seamless>'
        + '<a href="%s">Embedded Bandcamp Link</a>' % urlstr
        + '</iframe>')

    return markup

def get_standard_bbc_parser(embed_images=True, escape_html=True):
    def context_sensitive_linker(url, context):
        try:
            return _video_markup_for_url(url)
        except EmbeddingNotSupportedException:
            return '<a href="%s">%s</a>' % (url, url)

    parser = bbcode.Parser(
        escape_html=escape_html,
        linker_takes_context=True,
        linker=context_sensitive_linker)

    if embed_images:
        parser.add_simple_formatter(
            'img',
            ('<a class="img-embed" href="%(value)s">'
                '<img src="%(value)s">'
            '</a>'),
            replace_links=False,
            replace_cosmetic=False)
    else:
        parser.add_simple_formatter(
            'img',
            '<a class="img-link" href="%(value)s">embedded image</a>',
            replace_links=False,
            replace_cosmetic=False)

    parser.add_simple_formatter(
        'byusingthistagIaffirmlannyissupercool',
        '<span class="ex">%(value)s</span>')

    def render_quote(tag_name, value, options, parent, context):
        author = options.get('author', None)
        pk = options.get('pk', None)

        if author:
            attribution = 'Originally posted by %s' % author

            if pk:
                try:
                    url = reverse('post', kwargs={'post_id': pk})
                except:
                    # Almost certianly NoReverseMatch in which case roll on
                    # but let's catch everything just in case
                    pass
                else:
                    attribution = 'Originally posted by <a href="%s">%s</a>' % (
                        url, author)

            template = """
                <blockquote>
                  <small class="attribution">%s</small>
                  %s
                </blockquote>
            """

            return template % (attribution, value)

        else:
            return '<blockquote>%s</blockquote>' % value

    parser.add_formatter('quote',
                         render_quote,
                         strip=True,
                         swallow_trailing_newline=True)

    def render_video(tag_name, value, options, parent, context):
        try:
            return _video_markup_for_url(value)
        except EmbeddingNotSupportedException:
            return '[video]%s[/video]' % value
    
    parser.add_formatter('video', render_video, render_embedded=False,
                         replace_cosmetic=False, replace_links=False)

    def render_code(tag_name, value, options, parent, context):
        return '<pre class="code-block">%s</pre>' % value

    parser.add_formatter('code', render_code, replace_cosmetic=False,
                         render_embedded=False)

    def render_bc(tag_name, value, options, parent, context):
        return ('<a class="unproc-embed" href="%s">embedded bandcamp link</a>'
                % value)

    parser.add_formatter('bc', render_bc, replace_cosmetic=False,
                         replace_links=False)

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

    c_parser.add_simple_formatter(
        'byusingthistagIaffirmlannyissupercool',
        '%(value)s')

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
