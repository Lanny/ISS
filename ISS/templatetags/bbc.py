from django import template
from django.utils import safestring
from django.utils.html import conditional_escape
from ISS import utils

register = template.Library()

@register.filter(name='bbc', needs_autoescape=True)
def bbc_format(value, embed_images=True, autoescape=True):
    if autoescape:
        value = conditional_escape(value)

    parser = utils.get_standard_bbc_parser(
            escape_html=False, 
            embed_images=embed_images)
    markup = parser.format(value)

    return safestring.mark_safe(markup)
