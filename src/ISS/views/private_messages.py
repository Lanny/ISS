from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponseBadRequest
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
        'pm_action_form': forms.PrivateMessageActionForm(),
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
        'pm_action_form': forms.PrivateMessageActionForm(),
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

    message.mark_read()

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
            try:
                quote_pk = int(request.GET['replyto'])
            except ValueError:
                raise PermissionDenied('You can\'t quote that!')

            rt = get_object_or_404(PrivateMessage, pk=quote_pk)

            if rt.inbox != request.user:
                raise PermissionDenied('You can\'t quote that!')

            if rt.subject.startswith(('re:', 'RE:')):
                initials['subject'] = rt.subject
            else:
                initials['subject'] = 're: ' + rt.subject

            initials['to'] = rt.sender.username
            initials['content'] = rt.quote_content()

        elif 'to' in request.GET:
            recipient = get_object_or_404(Poster, pk=request.GET['to'])
            initials['to'] = recipient.username

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

class PrivateMessageActions(utils.MethodSplitView):
    staff_required = False
    unbanned_required = True
    require_login = True

    def POST(self, request):
        form = forms.PrivateMessageActionForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'delete-message':
                return self._handle_delete_messages(request)
            else:
                raise Exception('Unexpected action.')
        else:
            return HttpResponseBadRequest('Invalid form.')

    @transaction.atomic
    def _handle_delete_messages(self, request):
        message_pks = request.POST.getlist('message', [])
        messages = [get_object_or_404(PrivateMessage, pk=pk) for pk in message_pks]

        for message in messages:
            if message.inbox != request.user:
                raise PermissionDenied('You can\'t delete that!')
            message.delete()

        target = request.POST.get('next', None)
        return HttpResponseRedirect(target)
