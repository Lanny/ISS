from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
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

@login_required
def sent(request):
    messages = (request.user
            .privatemessage_set
            .filter(sender=request.user)
            .order_by('-created'))

    items_per_page = utils.get_config('general_items_per_page')
    paginator = Paginator(messages, items_per_page)
    page = utils.page_by_request(paginator, request)

    ctx = {
        'messages': page,
        'page_name': 'Sent',
        'active_tab': 'sent',
        'show_from': False,
        'show_to': True,
        'breadcrumbs': [
            ('Private Messages', ''),
            ('Sent', 'sent-pms')
        ]
    }

    return render(request, 'private_messages/pm_list.html', ctx)




@login_required
def read_pm(request, pm_id):
    message = get_object_or_404(PrivateMessage, pk=pm_id)

    if message.inbox != request.user:
        raise PermissionDenied('You can\'t read that!')

    is_sender = message.sender == request.user
    is_receiver = message.receiver == request.user

    active_tab = None
    if is_sender:
        active_tab = 'sent'
    elif is_receiver:
        active_tab = 'inbox'

    ctx = {
        'message': message,
        'page_name': 'Message: %s' % message.subject,
        'active_tab': active_tab,
        'breadcrumbs': [
            ('Private Messages', '')
        ]
    }

    if is_sender:
        ctx['breadcrumbs'].append(('Sent', 'sent-pms'))
    if is_receiver:
        ctx['breadcrumbs'].append(('Inbox', 'inbox'))

    ctx['breadcrumbs'].append(('Message: %s' % message.subject,''))

    return render(request, 'private_messages/pm_view.html', ctx)
    
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
        initials = {}
        if 'replyto' in request.GET:
            rt = get_object_or_404(PrivateMessage, pk=request.GET['replyto'])

            if rt.inbox != request.user:
                raise PermissionDenied('You can\'t quote that!')

            if rt.subject.startswith(('re:', 'RE:')):
                initials['subject'] = rt.subject
            else:
                initials['subject'] = 're: ' + rt.subject

            initials['to'] = rt.sender.username
            initials['content'] = rt.quote_content()

        form = forms.NewPrivateMessageForm(author=request.user, initial=initials)
        
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

