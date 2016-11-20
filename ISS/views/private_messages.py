from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from ISS import utils, forms
from ISS.models import *

@login_required
def inbox(request):
    messages = (request.user
            .privatemessage_set
            .filter(receiver=request.user)
            .order_by('-created'))

    items_per_page = utils.get_config('general_items_per_page')
    paginator = Paginator(messages, items_per_page)
    page = utils.page_by_request(paginator, request)

    ctx = {
        'messages': page,
        'page_name': 'Inbox',
        'active_tab': 'inbox',
        'show_from': True,
        'show_to': False,
        'breadcrumbs': [
            ('Private Messages', ''),
            ('Inbox', 'inbox')
        ]
    }

    return render(request, 'private_messages/pm_list.html', ctx)
    
class NewPrivateMessage(utils.MethodSplitView):
    login_required = True
    active_required = True

    ctx_defaults = {
        'page_name': 'Compose New Private Message',
        'active_tab': 'compose',
        'breadcrumbs': [
            ('Private Messages', ''),
            ('Compose', 'compose-pm')
        ]
    }

    def GET(self, request):
        form = forms.NewPrivateMessageForm(author=request.user)
        
        ctx = { 'form': form }
        ctx.update(self.ctx_defaults)

        return render(request, 'private_messages/compose.html', ctx)

    def POST(self, request):
        form = forms.NewPrivateMessageForm(request.POST, author=request.user)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('inbox'))

        else:
            ctx = { 'form': form }
            ctx.update(self.ctx_defaults)

            return render(request, 'private_messages/compose.html', ctx)

