import urlparse
import urllib2
import re
import os
import datetime
import bbcode
import collections
import importlib
import json
import random

from lxml import etree

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator, Page
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, \
    HttpResponseForbidden
from django.utils import html
from django.shortcuts import render
from snowpenguin.django.recaptcha2.fields import ReCaptchaField

from ISS.models import *
from ISS import iss_bbcode

DO_NOT_LINK_TAGS = { 'video', 'pre' }
TIME_DELTA_FORMAT = re.compile(r'^\s*((?P<years>\d+)y)?\s*((?P<weeks>\d+)w)?\s*((?P<days>\d+)d)?\s*((?P<hours>\d+?)h)?\s*((?P<minutes>\d+?)m)?\s*((?P<seconds>\d+?)s)?\s*$')
TIME_HIERARCHY = (
    ('years', 356 * 24 * 60 * 60),
    ('weeks', 7 * 24 * 60 * 60),
    ('days', 24 * 60 * 60),
    ('hours', 60 * 60),
    ('minutes', 60),
    ('seconds', 1)
)
SECONDS_IN = dict(TIME_HIERARCHY)

class GlobShortcodeRegistrar(object):
    _directory = None

    def __init__(self, directory):
        self._directory = directory

    def get_shortcode_map(self):
        sc_map = {}

        try:
            files = os.listdir(os.path.join('ISS/static', self._directory))
        except OSError:
            files = []

        for filename in files:
            match = re.match(r'(.+)\.(gif|png|jpg)', filename)

            if not match:
                continue
            
            name, ext = match.groups()
            sc_map[name] = name + '.' + ext

        return sc_map

config_defaults = {
    'forum_name': 'INTERNATIONAL SPACE STATION',
    'forum_domain': 'yourdomain.space',
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
    'static_pages': (),
    'humans': (
        ('Lead Alcoholic', 'Ryan "Lanny" Jenkins', 'lan.rogers.book@gmail.com'),
        ('Pedophile Tech Support', 'Sophie', ''),
    ),
    'shortcode_registrar': GlobShortcodeRegistrar('img/gif/'),
    'client_ip_field': 'REMOTE_ADDR',
    'extensions': [],
    'extension_config': {},
    'min_account_age_to_anonymize': datetime.timedelta(days=28),
    'min_posts_to_anonymize': 151,
    'initial_account_period_total': 150,
    'initial_account_period_width': datetime.timedelta(days=1),
    'initial_account_period_limit': 20,
    'captcha_period': 0,
    'enable_registration': True,
    'enable_invites': False,
    'invite_expiration_time': datetime.timedelta(days=14),
    'themes': (
        ('&T', '&T'),
        ('bibliotek', 'Bibliotek')
    ),
    'default_theme': '&T'
}

config = config_defaults.copy()
config.update(settings.FORUM_CONFIG)

for extension in config['extensions']:
    module = importlib.import_module(extension)
    ext_config = getattr(module, 'ISS_config', {}).copy()
    ext_config.update(config['extension_config'].get(extension, {}))

    config['extension_config'][extension] = ext_config

config['title_ladder'] = sorted(config['title_ladder'], key=lambda x: x[0],
                                reverse=True)

our_humans = config_defaults['humans'] 
their_humans = settings.FORUM_CONFIG.get('humans', ()) 
config['humans'] = our_humans + their_humans

config['shortcode_map'] = config['shortcode_registrar'].get_shortcode_map()

class MethodSplitView(object):
    """
    A flexible class for splitting handling of different HTTP methods being
    dispatched to the same view into separate class methods. Subclasses may
    define a separate class method for each HTTP method the view handles (e.g.
    GET(self, request, ...), POST(self, request, ...) which will be called with
    the usual view signature when that sort of request is made.
    
    Subclasses may also define a `pre_method_check` method which, if it returns
    a HttpResponse, will be used to response to the request instead of
    delegating to the corresponding method.
    """

    _MAGIC = 'haderach kwisatz'

    def __init__(self, magic='melange', *args, **kwargs):
        if magic != self._MAGIC:
            raise RuntimeError(
                'MethodSplitViews should be instantiated through the '
                '.as_view() method, not directly. Check your urls file.')

    def __call__(self, request, *args, **kwargs):
        if getattr(self, 'active_required', False):
            if not request.user.is_active:
                return HttpResponseForbidden('You must be an active user '
                                             'to do this')
        if getattr(self, 'staff_required', False):
            if not request.user.is_staff:
                return HttpResponseForbidden('You must be staff to do this.')

        if getattr(self, 'unbanned_required', False):
            if not request.user.is_authenticated() :
                return HttpResponseForbidden(
                    'You must be authenticated to take this action.')

            if request.user.is_banned():
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
        view = cls(magic=cls._MAGIC)
        if getattr(cls, 'require_login', False):
            return login_required(view)
        else:
            return view

def memoize(f):
    memo = {}
    def memoized(*args):
        if args not in memo:            
            memo[args] = f(*args)

        return memo[args]

    return memoized

def get_config(key=None):
    if not key:
        return config
    else:
        return config.get(key)

def get_ext_config(ext, key=None):
    if not key:
        return config['extension_config'][ext]
    else:
        return config['extension_config'][ext].get(key)

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


def get_standard_bbc_parser(embed_images=True, embed_video=True,
                            allow_js=True, escape_html=True):
    return iss_bbcode.build_parser((
            'IMG' if embed_images else 'NO_IMG',
            'VIDEO' if embed_video else 'NO_VIDEO',
            'BYUSINGTHISTAGIAFFIRMLANNYISSUPERCOOL',
            'QUOTE',
            'CODE',
            'BC',
            'LINK',
            'SPOILER' if allow_js else 'NOJS_SPOILER',
            'PGP' if allow_js else 'NOP',
            'SHORTCODE'
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

        if field in ('has_unread_posts', 'is_subscribed', 'get_jump_post', 'has_been_read'):
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

    seconds = 0
    for (name, comp) in parts.groupdict().items():
        if comp:
            seconds += int(comp) * SECONDS_IN[name]

    return datetime.timedelta(seconds=seconds)

def format_duration(duration):
    seconds = duration.total_seconds()
    parts = []

    for (unit_name, nsecs) in TIME_HIERARCHY:
        if seconds >= nsecs:
            (q, r) = divmod(seconds, nsecs)
            parts.append('%d%s' % (q, unit_name[0]))
            seconds = r 

        if seconds < 1:
            break

    return ' '.join(parts)

_js_spoiler_template = '''
    <div class="spoiler closed">
        <button class="tab" type="button">
            <span class="label">Show</span>
            <span class="name">%s</span>
        </button>
        <div class="content" data-content="%s"></div>
    </div>
'''

_nojs_spoiler_template = '''
    <div class="nojs-spoiler spoiler">
        <input id="sp-%(id)s" type="checkbox" class="spoiler-hack-checkbox" />
        <label class="tab" for="sp-%(id)s">
            <span class="label"></span>
            <span class="name">%(name)s</span>
        </label>
        <div class="content">
            %(content)s
        </div>
    </div>
'''

def render_spoiler(content, name='spoiler', js_enabled=True):
    # NOTE: it may look odd to you that we're escaping HTML content in the JS
    # enabled case but not in the nojs case. This is correct so don't change
    # it. The reason for this is that the content is already HTML escaped, but
    # in the JS case it's 
    # 
    if js_enabled:
        return _js_spoiler_template % (name, html.escape(content))
    else:
        return _nojs_spoiler_template % {
            'content': content,
            'id': random.randint(0,2**32),
            'name': name
        }

class TolerantJSONEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return super(self, json.JSONEncoder).default(o)
        except TypeError:
            return None

class HomoglyphNormalizer(object):
    @classmethod
    def _decode_hex_repr(cls, s):
        return ('\\U%08x' % int(s, 16)).decode('unicode-escape')

    @classmethod
    def _decode_seq(cls, s):
        return u''.join(
            [cls._decode_hex_repr(point) for point in s.strip().split(' ')]
        )

    def __init__(self, confusables_file=None):
        if not confusables_file:
            base = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base, 'support/confusables.txt')
            confusables_file = open(path, 'r')

        self._norm_graph = {}

        with confusables_file:
            for line in confusables_file:
                # Strip off comments
                effective_line = line.split('#', 1)[0].strip()

                if effective_line.count(';') < 2:
                    continue

                confusable_seq, target_seq, _ = effective_line.split(';', 2)
                confusable = self._decode_seq(confusable_seq)
                target = self._decode_seq(target_seq)

                if self._norm_graph.has_key(confusable):
                    f.close()
                    raise ValueError('One confusable codepoint has multiple '
                                     'normalization targets.')

                self._norm_graph[confusable] = target

    def _norm_codepoint(self, code_point):
        if self._norm_graph.has_key(code_point):
            return self._norm_graph[code_point]
        else:
            return code_point

    def normalize(self, unicode_str):
        if not isinstance(unicode_str, unicode):
            unicode_str = unicode(unicode_str)

        normalized = []
        for code_point in unicode_str:
            normalized.append(self._norm_codepoint(code_point.lower()))
            normalized.append(self._norm_codepoint(code_point.upper()))

        return u''.join(normalized)

_process_normalizer = None
def normalize_homoglyphs(prenormalized):
    global _process_normalizer
    if not _process_normalizer:
        _process_normalizer = HomoglyphNormalizer()

    return _process_normalizer.normalize(prenormalized)

def captchatize_form(form, label="Captcha"):
    _config = get_config('recaptcha_settings')

    if _config:
        class NewForm(form):
            captcha = ReCaptchaField(label=label,
                                     public_key=_config[0],
                                     private_key=_config[1])

        return NewForm

    else:
        return form

GENERIC_CAPTCHA_LABEL = 'Captcha (required for your first %d posts)' % (
    get_config('captcha_period')
)

def conditionally_captchatize(request, Form):
    if not request.user.is_authenticated():
        return Form

    post_count = request.user.post_set.count()

    if post_count < get_config('captcha_period'):
        return captchatize_form(Form, label=GENERIC_CAPTCHA_LABEL)
    else:
        return Form
    

