import os
import os.path
import re
import random

from django.conf import settings

config_defaults = {
    'forum_name': 'INTERNATIONAL SPACE STATION',
    'banner_dir': 'banners'
}

config = config_defaults.copy()
config.update(settings.FORUM_CONFIG)

banners = os.listdir(os.path.join('ISS/static', config['banner_dir']))
banners = [x for x in banners if re.match(r'.*\.(gif|png|jpg)', x)]

def banner(request):
    banner_name = random.choice(banners)

    return {
        'banner': os.path.join(config['banner_dir'], banner_name)
    }

def forum_config(request):
    return {'config': config}
