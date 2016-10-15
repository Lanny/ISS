from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404

import utils
import forms
from .models import *

class MethodSplitView(object):
    def __call__(self, request, *args, **kwargs):
        meth_name = ('AJAX_' if request.is_ajax() else '') + request.method

        meth = getattr(self, meth_name, None)

        if not meth:
            return HttpResponseBadRequest('Request method %s not supported'
                                          % request.method)
        
        return meth(request, *args, **kwargs)

    @classmethod
    def as_view(cls):
        if getattr(cls, 'require_login', False):
            return login_required(cls())
        else:
            return cls()

def forum_index(request):
    forums = Forum.objects.all()
    ctx = { 'forums': forums }

    return render(request, 'forum_index.html', ctx)

def thread_index(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    threads = forum.thread_set.order_by('-created')
    paginator = Paginator(threads, 30)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'forum': forum,
        'threads': page
    }

    return render(request, 'thread_index.html', ctx)

def thread(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    posts = thread.post_set.order_by('created')
    paginator = Paginator(posts, 30)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'thread': thread,
        'posts': page
    }

    return render(request, 'thread.html', ctx)

class NewThread(MethodSplitView):
    login_required = True

    def GET(self, request, forum_id):
        forum = get_object_or_404(Forum, pk=forum_id)
        form = forms.NewThreadForm(initial={ 'forum':forum })
        
        ctx = {
            'forum': forum,
            'form': form
        }

        return render(request, 'new_thread.html', ctx)

    def POST(self, request, forum_id):
        forum = get_object_or_404(Forum, pk=forum_id)
        form = forms.NewThreadForm(request.POST)

        if form.is_valid():
            thread = form.save(request.user)
            return HttpResponseRedirect(thread.get_url())

        else:
            ctx = {
                'forum': forum,
                'form': form
            }

            return render(request, 'new_thread.html', ctx)
