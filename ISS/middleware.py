import pytz

from django.utils import timezone

class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            timezone.activate(pytz.timezone(request.user.timezone))
        else:
            timezone.activate('UTC')

        return None
