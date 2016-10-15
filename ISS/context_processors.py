import os
import os.path
import re
import random

from ISS import utils


banners = os.listdir(os.path.join('ISS/static', utils.get_config('banner_dir')))
banners = [x for x in banners if re.match(r'.*\.(gif|png|jpg)', x)]

def banner(request):
    banner_name = random.choice(banners)

    return {
        'banner': os.path.join(utils.get_config('banner_dir'), banner_name)
    }

def forum_config(request):
    return {'config': utils.get_config()}
