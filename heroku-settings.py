import os
import dj_database_url

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

if 'ALLOWED_HOST' in os.environ:
    ALLOWED_HOSTS.append(os.environ['ALLOWED_HOST'])

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'snowpenguin.django.recaptcha2',
    'Houston',
    'ISS',
    'ISS.contrib.taboo'
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ISS.middleware.TimezoneMiddleware',
    'ISS.middleware.PMAdminMiddleware',
    'ISS.middleware.IPBanMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'ISS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ISS.context_processors.banner',
                'ISS.context_processors.forum_config',
                'ISS.context_processors.user_config',
                'ISS.context_processors.private_messages'
            ],
        },
    },
]

WSGI_APPLICATION = 'ISS.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True),
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '.staticroot')

AUTH_USER_MODEL = 'ISS.Poster'
FORUM_CONFIG = {
    'extensions': []
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'ISS.auth.backends.vB5_legacy'
]

LOGIN_URL = '/login'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'NIS-default',
    },
    'db_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'NIS-db',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

MEDIA_ROOT = '/media'
MEDIA_URL = '/media/'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
