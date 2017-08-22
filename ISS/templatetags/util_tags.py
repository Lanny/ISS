from django import template
from django.template import defaultfilters

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
