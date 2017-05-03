from django import template

from ISS.models import FilterWord

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
