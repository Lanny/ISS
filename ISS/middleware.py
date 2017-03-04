import pytz
import traceback

from django.conf import settings
from django.utils import timezone

from ISS.models import *

class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            timezone.activate(pytz.timezone(request.user.timezone))
        else:
            timezone.activate('UTC')

        return None

class PMAdminMiddleware(object):
    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None

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
                traceback.format_exc(exception))

        PrivateMessage.send_pm(
            Poster.get_or_create_system_user(),
            Poster.objects.filter(is_admin=True),
            'Error encountered in processing request',
            message)

        return None
