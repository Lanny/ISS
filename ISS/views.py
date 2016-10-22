from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
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
    forums = Forum.objects.all().order_by('priority')
    ctx = { 'forums': forums }

    return render(request, 'forum_index.html', ctx)

def thread_index(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    threads = forum.thread_set.order_by('-last_update')
    paginator = utils.MappingPaginator(threads, 30)

    paginator.install_map_func(lambda t: utils.ThreadFascet(t, request))

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
    reply_form = forms.NewPostForm(initial={ 'thread': thread })

    page = utils.page_by_request(paginator, request)

    ctx = {
        'thread': thread,
        'posts': page,
        'reply_form': reply_form
    }

    response = render(request, 'thread.html', ctx)

    # Update thread flag
    if request.user.is_authenticated():
        thread.mark_read(request.user, page[-1])

    return response


class NewThread(MethodSplitView):
    login_required = True

    def GET(self, request, forum_id):
        forum = get_object_or_404(Forum, pk=forum_id)
        form = forms.NewThreadForm(initial={ 'forum': forum })
        
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

class NewReply(MethodSplitView):
    login_required = True

    def GET(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        form = forms.NewPostForm(initial={ 'thread': thread })
        
        ctx = {
            'thread': thread,
            'form': form
        }

        return render(request, 'new_post.html', ctx)

    def POST(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        form = forms.NewPostForm(request.POST)

        if form.is_valid():
            post = form.save(request.user)
            return HttpResponseRedirect(post.get_url())

        else:
            ctx = {
                'thread': thread,
                'form': form
            }

            return render(request, 'new_post.html', ctx)

class LoginUser(MethodSplitView):
    def GET(self, request):
        form = AuthenticationForm()
        ctx = {'form': form}
        return render(request, 'login.html', ctx)

    def POST(self, request):
        logout(request)
        if request.POST:
            form = AuthenticationForm(data=request.POST, request=request)

            if form.is_valid():
                print ' JAZZ!'
                print form.user_cache
                print form.user_cache.backend
                login(request, form.user_cache)
                next_url = request.POST.get('next', '/')
                return HttpResponseRedirect(next_url)

            else:
                ctx = {'form': form}
                return render(request, 'login.html', ctx)

class LogoutUser(MethodSplitView):
    def POST(self, request):
        logout(request)

        next_url = request.POST.get('next', '/')
        return HttpResponseRedirect(next_url)

class RegisterUser(MethodSplitView):
    def GET(self, request):
        form = forms.RegistrationForm()
        ctx = {'form': form}

        return render(request, 'register.html', ctx)

    def POST(self, request):
        form = forms.RegistrationForm(request.POST)

        if form.is_valid():
            poster = form.save(commit=True)

            # Ceremoniously call authenticate so login will succeed
            poster = authenticate(username = form.cleaned_data['username'],
                                  password = form.cleaned_data['password1'])
            login(request, poster)
            return HttpResponseRedirect('/')

        else:
            ctx = { 'form': form }

            return render(request, 'register.html', ctx)


