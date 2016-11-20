from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from ISS import utils, forms
from ISS.models import *

def inbox(request):
    messages = (request.user
            .privatemessage_set
            .all()
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
    

