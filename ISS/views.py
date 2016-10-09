from django.shortcuts import render
from django.core.paginator import Paginator

import utils
from .models import *

def forum_index(request):
    forums = Forum.objects.all()
    ctx = { 'forums': forums }

    return render(request, 'forum_index.html', ctx)

def thread_index(request, forum_id):
    forum = Forum.objects.get(pk=forum_id)
    threads = forum.thread_set.order_by('-created')
    paginator = Paginator(threads, 30)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'forum': forum,
        'threads': page
    }

    return render(request, 'thread_index.html', ctx)
