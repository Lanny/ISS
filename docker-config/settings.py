# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%ve+iy6_#4jxw7n#(&n1yyqbr*%!(9v=634@u_u!a*03j3bca5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

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
    'ISS',
    'ISS.contrib.taboo',
    'django_probes'
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
    'ISS.middleware.CSPMiddleware',
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


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql_psycopg2',
        'NAME':     'iss',
        'USER':     'iss_user',
        'PASSWORD': 'this0is0a0super0secret0password69',
        'HOST':     'db',
        'PORT':     '',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

AUTH_USER_MODEL = 'ISS.Poster'

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

MEDIA_ROOT = '/media'
MEDIA_URL = '/media/'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

FORUM_CONFIG = {
    'extensions': [],
    'initial_account_period_total': 1,
    'disable_captchas': False,
    'captcha_period': 0,
    'initial_account_period_total': 0,
    'new_accounts_require_approval': True,
}
