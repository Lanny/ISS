import urlparse
import urllib2
import re
import datetime
import bbcode
import collections

from lxml import etree

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator, Page
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, \
    HttpResponseForbidden
from django.shortcuts import render

from ISS.models import *
from ISS import iss_bbcode

DO_NOT_LINK_TAGS = { 'video', 'pre' }
TIME_DELTA_FORMAT = re.compile(r'^\s*((?P<days>\d+)d)?\s*((?P<hours>\d+?)h)?\s*((?P<minutes>\d+?)m)?\s*$')

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
    'max_embedded_items': 5,
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
                return HttpResponseForbidden('You must be an active user '
                                             'to do this')
        if getattr(self, 'staff_required', False):
            if not request.user.is_staff:
                return HttpResponseForbidden('You must be staff to do this.')

        if getattr(self, 'unbanned_required', False):
            if not request.user.is_authenticated() or request.user.is_banned():
                return get_ban_403_response(request)

        meth = getattr(self, request.method, None)

        if not meth:
            return HttpResponseBadRequest('Request method %s not supported'
                                          % request.method)
        
        response_maybe = self.pre_method_check(request, *args, **kwargs)

        if isinstance(response_maybe, HttpResponse):
            return response_maybe

        return meth(request, *args, **kwargs)

    def pre_method_check(request, *args, **kwargs):
        return None

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

def get_ban_403_response(request):
    bans = request.user.get_pending_bans().order_by('-end_date')

    ctx = {
        'end_date': bans[0].end_date,
        'reasons': [ban.reason for ban in bans],
        'staff': auth.get_user_model().objects.filter(is_staff=True)
    }

    return render(request, 'ban_notification.html', ctx, status=403)

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
    return iss_bbcode.build_parser((
            'IMG' if embed_images else 'NO_IMG',
            'VIDEO' if embed_images else 'NO_IMG',
            'BYUSINGTHISTAGIAFFIRMLANNYISSUPERCOOL',
            'QUOTE',
            'CODE',
            'BC',
            'LINK'
        ), escape_html=escape_html)

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

def get_tag_distribution(data):
    """
    Parses a BBCode string and returns a dictionary with keys being tags
    and values being a count of how many times that type of tag occurs. Both
    paired and standalone tags are counted exactly once.
    """
    tag_counts = collections.defaultdict(int)
    parser = get_standard_bbc_parser()

    for token_type, tag_name, _, _ in parser.tokenize(data):
        if token_type == parser.TOKEN_TAG_START:
            tag_counts[tag_name] += 1

    return tag_counts

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

def parse_duration(time_str):
    parts = TIME_DELTA_FORMAT.match(time_str)
    if not parts:
        return

    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)

    return datetime.timedelta(**time_params)
