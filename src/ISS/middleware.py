import pytz
import traceback
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from django.http import Http404
from django.core.exceptions import PermissionDenied

from ISS import utils
from ISS.models import *

class BaseMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

class IPBanMiddleware(BaseMiddleware):
    def __call__(self, request):
        ip_addr = request.META.get(utils.get_config('client_ip_field'), None)

        if IPBan.objects.filter(on=ip_addr).count() > 0:
            raise PermissionDenied('Fuck right off')
        else:
            return self.get_response(request)


class TimezoneMiddleware(BaseMiddleware):
    def __call__(self, request):
        if request.user.is_authenticated:
            timezone.activate(pytz.timezone(request.user.timezone))
        else:
            timezone.activate('UTC')

        return self.get_response(request)

class PMAdminMiddleware(BaseMiddleware):
    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None
        
        if isinstance(exception, (Http404, PermissionDenied)):
            # No need to report 404s
            return None

        formatted = traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
        )

        message = '''
            Encountered exception when processing request.
            Request Path: %s
            Request Method: %s
            Active User: %s

            Stack Trace:
            [code]%s[/code]
        ''' % (
            request.path,
            request.method,
            request.user,
            ''.join(formatted)
        )

        PrivateMessage.send_pm(
            Poster.get_or_create_system_user(),
            Poster.objects.filter(is_admin=True),
            'Error encountered in processing request',
            message)

        return None

CSP_BASE = '; '.join([
    key + ' ' + ' '.join(value)
    for (key, value)
    in {
        'default-src': ["'self'", "'nonce-%s'"],
        'style-src-attr': ["'unsafe-inline'"],
        'img-src': ['*', 'data:'],
        'media-src': ['*'],
        'frame-src': [
            'https://www.youtube.com',
            'https://www.bitchute.com',
            'https://bandcamp.com',
        ],
        'object-src': ["'none'"],
    }.items()
])

class CSPMiddleware(BaseMiddleware):
    def __call__(self, request):
        nonce = 'wariat-' + uuid4().hex

        request.NONCE = nonce
        response = self.get_response(request)
        response['Content-Security-Policy'] = CSP_BASE % nonce

        return response
