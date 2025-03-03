import datetime
import importlib

from django.conf import settings

from .GlobShortcodeRegistrar import GlobShortcodeRegistrar
from .Singleton import Singleton
from . import misc


class ConfigurationManager(Singleton):
    CONFIG_DEFAULTS = {
        'forum_name': 'INTERNATIONAL SPACE STATION',
        'forum_domain': 'yourdomain.space',
        'default_protocol': 'http',
        'email_host_blacklist': [],
        'banner_dir': 'banners',
        'min_post_chars': 1,
        'max_post_chars': 19475, # No. characters in the first chapter of Dune
        'min_thread_title_chars': 1,
        'threads_per_forum_page': 20,
        'posts_per_thread_page': 20,
        'general_items_per_page': 20,
        'ninja_edit_grace_time': 120,
        'private_message_flood_control': 30,
        'max_embedded_items': 5,
        'title_ladder': (
            (100, 'Regular'),
            (10, 'Acolyte'),
            (0, 'Novice')
        ),
        'recaptcha_settings': None,
        'max_avatar_size': 128*1024,
        'junk_user_username': 'The Self Taught Man',
        'system_user_username': 'Wintermute',
        'report_message': 'Select a reason for reporting this post:',
        'report_reasons': (
            ('SPAM_BOT', 'Spam bot/spamming script'),
            ('ILLEGAL_CONTENT', 'Illegal content'),
            ('INTENTIONAL_DISRUPTION', 'Intentional disruption')
        ),
        'control_links': (
            ('RLINK', 'Subscriptions', 'usercp', 'is_authenticated', None),
            ('RLINK', 'Latest Threads', 'latest-threads', 'always', None),
            ('PMS', 'Inbox', 'inbox', 'is_authenticated', None),
            ('RLINK', 'Search', 'search', 'always', None),
            ('RLINK', 'Members List', 'members', 'always', None),
            ('RLINK', 'Admin', 'admin:index', 'is_admin', None),
            ('FORM', 'Logout', 'logout', 'is_authenticated', 'logout-form'),
            ('RLINK', 'Register', 'register', 'is_not_authenticated', None),
        ),
        'static_pages': (),
        'humans': (
            ('Lead Alcoholic', 'Ryan "Lanny" Jenkins', 'lan.rogers.book@gmail.com'),
            ('Pedophile Tech Support', 'Sophie', ''),
        ),
        'shortcode_registrar': GlobShortcodeRegistrar('img/gif/'),
        'client_ip_field': 'REMOTE_ADDR',
        'extensions': [],
        'extension_config': {},
        'min_account_age_to_anonymize': datetime.timedelta(days=28),
        'min_posts_to_anonymize': 151,
        'initial_account_period_total': 150,
        'initial_account_period_width': datetime.timedelta(days=1),
        'initial_account_period_limit': 20,
        'captcha_period': 0,
        'enable_registration': True,
        'require_email_verification': True,
        'enable_invites': False,
        'invite_expiration_time': datetime.timedelta(days=14),
        'themes': {
            '&T': {'name': '&T', 'color': '#D5DEE5'},
            'bibliotek': {'name': 'Bibliotek', 'color': '#FFFFFF'},
            'amoled': {'name': 'AMOLED', 'color': '#000000'},
            'everforest-dark-hard': {'name': 'Everforest', 'color': '#272e33'},
            'watermelon-dark': {'name': 'Watermelon Dark', 'color': '#e48c85'},
            'halloween': {'name': 'Haloween 2024', 'color': '#FF7B00'},
            'turkey-tina': {'name': 'Turkey Tina', 'color': '#EAAC64'},
            'frotse': {'name': 'Frotse', 'color': '#AEC3A4'},
        },
        'default_theme': '&T',
    }

    def reinit(self, overrides):
        """
        Exists only for purposes of testing. Never use this in actual code.
        """
        self._config = misc.rmerge(self.CONFIG_DEFAULTS.copy(), overrides)
        self._config['DEBUG'] = settings.DEBUG

        # Turn the blacklist into a set for faster lookups
        self._config['email_host_blacklist'] = set(
            self._config['email_host_blacklist'])
        

        for extension in self._config['extensions']:
            module = importlib.import_module(extension)
            ext_config = getattr(module, 'ISS_config', {}).copy()
            ext_config.update(
                self._config['extension_config'].get(extension, {}))
            self._config['extension_config'][extension] = ext_config
            self._config['title_ladder'] = sorted(self._config['title_ladder'],
                                                  key=lambda x: x[0],
                                                  reverse=True)

        our_humans = self.CONFIG_DEFAULTS['humans'] 
        their_humans = overrides.get('humans', ()) 
        self._config['humans'] = our_humans + their_humans

        registrar = self._config['shortcode_registrar']
        self._config['shortcode_map'] = registrar.get_shortcode_map()

    def __init__(self, overrides=None):
        if overrides is None:
            overrides = settings.FORUM_CONFIG

        self.reinit(overrides=overrides)

    def get(self, *keys):
        if len(keys) == 0:
            return self._config
        elif len(keys) == 1:
            return self._config.get(keys[0])
        else:
            return tuple(self._config.get(key) for key in keys)

    def get_ext(self, ext, *keys):
        ext_config = self._config['extension_config'][ext]

        if len(keys) == 0:
            return ext_config
        elif len(keys) == 1:
            return ext_config.get(keys[0])
        else:
            return tuple(ext_config.get(key) for key in keys)

    def set(self, key_path, value):
        """
        Exists only for purposes of testing. Never use this in actual code.
        """
        if isinstance(keys, str):
            key_path = (key_path,)

        target = self._config
        
        for key in key_path[:-1]:
            target = target[key_path]

        target[key_path[-1]] = value

def get_config(*keys):
    return ConfigurationManager.get_instance().get(*keys)
