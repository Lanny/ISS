import os
import os.path
import re
import random

from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from ISS.models import Banner
from ISS.forms import ISSAuthenticationForm
from ISS import utils


def get_banners():
    return Banner.objects.all().filter(is_enabled=True)

def banner(request):
    banners = cache.get_or_set('banners', get_banners, 60*60*24)
    print(banners)
    banner = random.choice(banners) if banners else None

    return { 'banner': banner }

def forum_config(request):
    return {'config': utils.get_config()}

def user_config(request):
    ctx = {}

    if isinstance(request.user, AnonymousUser):
        ctx['embed_images'] = True
        ctx['embed_video'] = True
        ctx['allow_avatars'] = True
        ctx['allow_js'] = True
        ctx['editor_buttons'] = False
        ctx['login_form'] = ISSAuthenticationForm()
    else:
        ctx['embed_images'] = request.user.embed_images()
        ctx['embed_video'] = request.user.embed_video()
        ctx['allow_js'] = request.user.allow_js
        ctx['editor_buttons'] = request.user.enable_editor_buttons
        ctx['allow_avatars'] = request.user.allow_avatars

    ctx['bbcode_settings'] = {
        'allow_js': ctx['allow_js'],
        'embed_images': ctx['embed_images'],
        'embed_video': ctx['embed_video'],
    }

    return ctx

def private_messages(request):
    ctx = {}

    if not isinstance(request.user, AnonymousUser):
        ctx['private_messages_count'] = request.user.get_inbox_badge_count()

    return ctx

