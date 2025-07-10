from django.http import HttpResponse, HttpResponseBadRequest, \
        HttpResponseForbidden

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ISS.utils.misc import get_ban_403_response

class MethodSplitView(object):
    """
    A flexible class for splitting handling of different HTTP methods being
    dispatched to the same view into separate class methods. Subclasses may
    define a separate class method for each HTTP method the view handles (e.g.
    GET(self, request, ...), POST(self, request, ...) which will be called with
    the usual view signature when that sort of request is made.
    
    Subclasses may also define a `pre_method_check` method which, if it returns
    a HttpResponse, will be used to response to the request instead of
    delegating to the corresponding method.
    """

    _MAGIC = 'haderach kwisatz'

    def __init__(self, magic='melange', *args, **kwargs):
        if magic != self._MAGIC:
            raise RuntimeError(
                'MethodSplitViews should be instantiated through the '
                '.as_view() method, not directly. Check your urls file.')

    def __call__(self, request, *args, **kwargs):
        if getattr(self, 'active_required', False):
            if not request.user.is_active:
                return HttpResponseForbidden('You must be an active user '
                                             'to do this')
        if getattr(self, 'staff_required', False):
            if not request.user.is_staff:
                return HttpResponseForbidden('You must be staff to do this.')

        if getattr(self, 'unbanned_required', False):
            if not request.user.is_authenticated:
                return HttpResponseForbidden(
                    'You must be authenticated to take this action.')

            if request.user.is_banned():
                return get_ban_403_response(request)

        if getattr(self, 'approval_required', False):
            if not request.user.is_authenticated:
                return HttpResponseForbidden(
                    'You must be authenticated to take this action.')

            if not request.user.is_approved:
                return render(request, 'unapproved_notification.html', status=403)

        meth = getattr(self, request.method, None)

        if not meth:
            return HttpResponseBadRequest('Request method %s not supported'
                                          % request.method)
        
        check_result = self.pre_method_check(request, *args, **kwargs)

        if isinstance(check_result, HttpResponse):
            return check_result

        if isinstance(check_result, dict):
            kwargs.update(check_result)

        return meth(request, *args, **kwargs)

    def pre_method_check(request, *args, **kwargs):
        return None

    @classmethod
    def as_view(cls):
        view = cls(magic=cls._MAGIC)
        if getattr(cls, 'require_login', False):
            return login_required(view)
        else:
            return view
