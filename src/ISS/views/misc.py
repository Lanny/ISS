from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden, HttpResponse)
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.csrf import csrf_exempt

from ISS import utils, forms, iss_bbcode
from ISS.models import *

class EchoForm(utils.MethodSplitView):
    def POST(self, request):
        content = request.POST.get('content', '')
        return HttpResponse(content, content_type='text/plain')

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(EchoForm, cls).as_view(*args, **kwargs)
        return csrf_exempt(view)

def view_static_page(request, page_id):
    page = get_object_or_404(StaticPage, page_id=page_id)
    ctx = {
        'page_title': page.page_title,
        'content': page.content
    }
    return render(request, 'static_page.html', ctx)

def humans(request):
    humans = utils.get_config('humans')

    s = '/* THOSE RESPONSIBLE */\n\n'

    for role, name, contact in humans:
        s += '%s: %s\nContact: %s\n\n' % (role, name, contact)

    top_posters = (Poster.objects.all()
        .annotate(num_posts=Count('post'))
        .order_by('-num_posts'))[:3]

    if top_posters:
        s += '\n/* TOP SHITPOSTERS */\n\n'

        for poster in top_posters:
            s += 'Top Shitposter: %s\nContact: %s\nDamage Done: %d\n\n' % (
                poster.username, poster.get_url(), poster.num_posts)

    return HttpResponse(s, content_type='text/plain')

def robots(request):
    robots = [
        '# ISS robots.txt, please crawl responsibly. We ask that you keep ',
        '# crawling to a few (as in less than 4) requests per second. Fully ',
        '# recursive crawling is acceptable under the condition that the ',
        '# disallowed urls are ignored for ranking operations as we maintain ',
        '# content the owners explicitly disavows (spam) for legal reasons ',
        '# under some of these urls.',
        '#',
        '# Please note that paginated thread lists like those matching ',
        '# /forum/\d+/ are sorted in reverse cronological order and their ',
        '# content is highly dynamic while most other paginated lists are ',
        '# append-only and will remain fairly stable.',
        'User-agent: *',
        'Disallow: /pms/',
        'Disallow: /api/',
        'Disallow: /embed/',
        '# The following urls are lists of posts, they are all available under',
        '# /thread/* which is their cannonical location for crawling',
        'Disallow: /search',
        'Disallow: /search/',
        'Disallow: /post/',
        'Disallow: /user/*/posts$',
        'Disallow: /user/*/thankedposts$',
        'Disallow: /user/*/poststhanked$',
        'Disallow: /user/*/threads$',
    ]

    for forum in Forum.objects.filter(is_trash=True):
        url = reverse('thread-index', args=(forum.pk,))
        robots.append('Disallow: %s' % url)

    return HttpResponse('\n'.join(robots), content_type='text/plain')

@cache_page(60 * 24 * 7)
@cache_control(max_age=60*24)
def smilies_css(request):
    return render(request, 'smilies.css', content_type='text/css')


