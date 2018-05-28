import os
import os.path
import re
import random

from django.contrib.auth.models import AnonymousUser

from ISS.forms import ISSAuthenticationForm
from ISS import utils

banners = os.listdir(os.path.join('ISS/static', utils.get_config('banner_dir')))
banners = [x for x in banners if re.match(r'.*\.(gif|png|jpg)', x)]

def banner(request):
    if not banners:
        return ''

    banner_name = random.choice(banners)

    return {
        'banner': os.path.join(utils.get_config('banner_dir'), banner_name)
    }

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

