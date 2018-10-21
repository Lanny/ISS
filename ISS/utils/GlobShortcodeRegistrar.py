import os
import re

class GlobShortcodeRegistrar(object):
    _directory = None

    def __init__(self, directory):
        self._directory = directory

    def get_shortcode_map(self):
        sc_map = {}

        try:
            files = os.listdir(os.path.join('ISS/static', self._directory))
        except OSError:
            files = []

        for filename in files:
            match = re.match(r'(.+)\.(gif|png|jpg)', filename)

            if not match:
                continue
            
            name, ext = match.groups()
            sc_map[name] = name + '.' + ext

        return sc_map

