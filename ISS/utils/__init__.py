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
from ISS.utils import misc


# Functions and classes defined in the misc submodule should be available as
# properties of the `utils` module, however some other utils submodules which
# can't import this module due to circularity require them as well. Utils
# submodules refer to `utils.misc.foo()` but consumers of the utils lib refer 
# to `utils.foo()` so here we're dumping the misc module's "exports" into our
# own.
for def_name in misc.__all__:
    locals()[def_name] = getattr(misc, def_name)

# We keep these classes in seperate files but would like to export them as part
# of this module directly rather than a submodule. This isn't super pretty but
# it makes working with them elsewhere a bit nicer.
CLASSES = (
    'HomoglyphNormalizer',
    'ConfigurationManager',
    'MethodSplitView',
)

for klass_name in CLASSES:
    module = importlib.import_module('.' + klass_name, __name__)
    locals()[klass_name] = getattr(module, klass_name)

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

def memoize(f):
    memo = {}
    def memoized(*args):
        if args not in memo:            
            memo[args] = f(*args)

        return memo[args]

    return memoized

def get_config(*keys):
    return ConfigurationManager.get_instance().get(*keys)

def get_ext_config(ext, *keys):
    return ConfigurationManager.get_instance().get_ext(ext, *keys)

def get_ban_403_response(request):
    bans = request.user.get_pending_bans().order_by('-end_date')

    ctx = {
        'end_date': bans[0].end_date,
        'reasons': [ban.reason for ban in bans],
        'staff': auth.get_user_model().objects.filter(is_staff=True)
    }

    return render(request, 'ban_notification.html', ctx, status=403)

def reverse_absolute(*args, **kwargs):
    return '%s://%s%s' % (
            get_config('default_protocol'),
            get_config('forum_domain'),
            reverse(*args, **kwargs))

def get_posts_per_page(poster):
    if poster.is_authenticated():
        return poster.posts_per_page
    else:
        return get_config('posts_per_thread_page')

def page_by_request(paginator, request):
    page_num = request.GET.get('p')

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page

def get_posts_page(qs, request):
    posts_per_page = get_posts_per_page(request.user)
    paginator = Paginator(qs, posts_per_page)
    page = page_by_request(paginator, request)

    return page

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
            'PGP' if allow_js else 'NOJS_PGP',
            'SHORTCODE'
        ), escape_html=escape_html)

def get_closure_bbc_parser():
    """
    BBCode parser that renders BBCode to BBCode, stripping quotes and easter
    eggs tags and removing PGP signatures, and . Typically used when quoting a
    post.
    """

    return iss_bbcode.build_parser(
        ('STRIP_PGP', 'STRIP_QUOTE', 'STRIP_COOL_TAG'),
        escape_html=False, newline='\n',
        install_defaults=False,
        replace_links=False,
        replace_cosmetic=False)

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
    

