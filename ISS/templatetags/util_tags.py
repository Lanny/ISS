from datetime import timedelta

from django import template
from django.template import defaultfilters
from django.urls import reverse
from django.contrib.staticfiles.templatetags import staticfiles

from ISS import utils
from ISS.models import FilterWord, AccessControlList

register = template.Library()

@register.assignment_tag
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

@register.simple_tag(name='get_theme')
def get_theme(user):
    if user.is_authenticated:
        theme_name = user.theme
    else:
        theme_name = utils.get_config('default_theme')

    return staticfiles.static("css/%s.css" % theme_name)

@register.simple_tag(name='url_apply')
def url_apply(pat, args_and_kwargs=None):
    args, kwargs = args_and_kwargs if args_and_kwargs else ((), {})
    return reverse(pat, args=args, kwargs=kwargs)

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

@register.filter
def poster_can_edit(post, poster):
    return post.can_be_edited_by(poster)

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
