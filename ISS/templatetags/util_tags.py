from datetime import timedelta

from django import template
from django.template import defaultfilters
from django.urls import reverse
from django.utils import html
from django.utils import safestring
from django.contrib.staticfiles.templatetags import staticfiles

from ISS import utils
from ISS.models import FilterWord, AccessControlList

register = template.Library()

@register.simple_tag
def test_link(test, user):
    if test == 'always':
        return True
    if test == 'is_authenticated':
        return user.is_authenticated()
    elif test == 'is_not_authenticated':
        return not user.is_authenticated()
    elif test == 'is_admin':
        return user.is_authenticated() and user.is_admin


@register.simple_tag(name='url_apply')
def url_apply(pat, args_and_kwargs=None):
    args, kwargs = args_and_kwargs if args_and_kwargs else ((), {})
    return reverse(pat, args=args, kwargs=kwargs)


def _get_theme(user):
    if user.is_authenticated:
        theme_name = user.theme
    else:
        theme_name = utils.get_config('default_theme')

    return theme_name


@register.simple_tag(name='get_theme')
def get_theme(user):
    return staticfiles.static("css/%s.css" % _get_theme(user))


@register.simple_tag(name='get_theme_color')
def get_theme_color(user):
    theme_code = _get_theme(user)
    default_theme = utils.get_config('default_theme')
    theme = utils.get_config('themes').get(theme_code, default_theme)
    return theme['color']


@register.simple_tag(name='pgp_block')
def pgp_block(pgp_key, js_enabled=True):
    markup = utils.render_spoiler(
        '<pre>' + html.escape(pgp_key) + '</pre>',
        name="PGP Public Key",
        js_enabled=js_enabled)

    return safestring.mark_safe(markup)


@register.inclusion_tag(
    'post_controls_itag.html',
    takes_context=True)
def post_controls(context):
    if '_iss_template_cache' not in context:
        context['_iss_template_cache'] = {}

    tcache = context['_iss_template_cache']
    user = context['user']
    post = context['post']

    if 'user_post_count' not in tcache:
        tcache['user_post_count'] = user.post_set.count()

    if 'user_is_banned' not in tcache:
        tcache['user_is_banned'] = user.is_banned()

    return {
        'user': user,
        'post': context['post'],
        'user_post_count': tcache['user_post_count'],
        'can_edit': post.can_be_edited_by(
            user,
            is_banned=tcache['user_is_banned']
        ),
    }


@register.filter(name='word_filter')
def word_filter(value):
    return FilterWord.do_all_replacements(value)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def check_acl(poster, acl_name):
    acl = AccessControlList.get_acl(acl_name)
    return acl.is_poster_authorized(poster)


@register.filter(expects_localtime=True, is_safe=False)
def present_dt(dt):
    return '%s at %s' % (
        defaultfilters.date(dt, 'Y-m-d'),
        defaultfilters.time(dt, 'f A e'))


@register.filter(expects_localtime=True, is_safe=False)
def present_td(td):
    if not isinstance(td, timedelta):
        return 'Forever'

    return utils.format_duration(td)
