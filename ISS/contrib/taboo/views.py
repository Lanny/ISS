from django.shortcuts import render
from ISS.utils import MethodSplitView

# Create your views here.

class Status(MethodSplitView):
    require_login = True
    unbanned_required = True

    def GET(self, request):
        return render(request, 'taboo/status.html', {})

class Register(MethodSplitView):
    pass

class Unregister(MethodSplitView):
    pass
