from django import template

register = template.Library()

@register.assignment_tag
def test_link(test, user):
    print test, user
    if test == 'always':
        return True
    if test == 'is_authenticated':
        return user.is_authenticated()
    elif test == 'is_not_authenticated':
        return not user.is_authenticated()
    elif test == 'is_admin':
        return user.is_authenticated() and user.is_admin
