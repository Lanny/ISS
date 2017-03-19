from django.contrib.auth import login, logout, authenticate, _get_backends
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, F
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden, HttpResponse)
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control, cache_page

from ISS import utils, forms
from ISS.models import *


@cache_control(no_cache=True, max_age=0, must_revalidate=True, no_store=True)
def forum_index(request):
    forums = Forum.objects.all().order_by('priority')
    ctx = {
        'forums': [utils.ForumFascet(f, request) for f in forums]
    }

    return render(request, 'forum_index.html', ctx)

@cache_control(no_cache=True, max_age=0, must_revalidate=True, no_store=True)
def thread_index(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    threads = forum.thread_set.order_by('-last_update')
    threads_per_page = utils.get_config('threads_per_forum_page')
    paginator = utils.MappingPaginator(threads, threads_per_page)

    paginator.install_map_func(lambda t: utils.ThreadFascet(t, request))

    page = utils.page_by_request(paginator, request)

    ctx = {
        'forum': forum,
        'threads': page
    }

    if request.user.is_authenticated():
        forum.mark_read(request.user)

    return render(request, 'thread_index.html', ctx)

def thread(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    posts = thread.post_set.order_by('created').select_related('author')
    page = utils.get_posts_page(posts, request)
    reply_form = forms.NewPostForm(author=request.user,
                                   initial={ 'thread': thread })

    ctx = {
        'thread': thread,
        'posts': page,
        'reply_form': reply_form
    }

    response = render(request, 'thread.html', ctx)

    # Update thread flag
    if request.user.is_authenticated():
        thread.mark_read(request.user, page[-1])

        if request.user.auto_subscribe == 2:
            thread.subscribe(request.user)

    return response

def redirect_to_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    thread = post.thread
    predecessors = (thread.get_posts_in_thread_order()
            .filter(created__lt=post.created)
            .count())
    page_num = predecessors / utils.get_posts_per_page(request.user)
    target_url = thread.get_url() + '?p=%d#post-%d' % (page_num + 1, post.pk)

    return HttpResponseRedirect(target_url)

def posts_by_user(request, user_id):
    poster = get_object_or_404(Poster, pk=user_id)
    posts = (poster.post_set
        .order_by('-created')
        .select_related('thread'))
    posts_per_page = utils.get_config('general_items_per_page')
    paginator = Paginator(posts, posts_per_page)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'poster': poster,
        'posts': page
    }

    return render(request, 'posts_by_user.html', ctx)

def thanked_posts(request, user_id):
    poster = get_object_or_404(Poster, pk=user_id)
    posts = (poster.post_set
        .filter(thanks__isnull=False)
        .annotate(Max('thanks__given'))
        .order_by('-thanks__given__max'))

    page = utils.get_posts_page(posts, request)

    ctx = {
        'poster': poster,
        'posts': page
    }

    return render(request, 'thanked_posts.html', ctx)

def posts_thanked(request, user_id):
    poster = get_object_or_404(Poster, pk=user_id)
    posts = (Post.objects.filter(thanks__thanker__id=user_id)
        .order_by('-created'))

    page = utils.get_posts_page(posts, request)

    ctx = {
        'poster': poster,
        'posts': page
    }

    return render(request, 'posts_thanked.html', ctx)


@cache_control(no_cache=True, max_age=0, must_revalidate=True, no_store=True)
def latest_threads(request):
    threads = (Thread.objects.all()
        .filter(forum__is_trash=False)
        .order_by('-last_update'))
    threads_per_page = utils.get_config('threads_per_forum_page')
    paginator = utils.MappingPaginator(threads, threads_per_page)

    paginator.install_map_func(lambda t: utils.ThreadFascet(t, request))

    page = utils.page_by_request(paginator, request)

    ctx = {
        'threads': page
    }

    return render(request, 'latest_threads.html', ctx)

@login_required
@cache_control(no_cache=True, max_age=0, must_revalidate=True, no_store=True)
def usercp(request):
    threads = (Thread.objects.all()
        .filter(
            threadflag__poster_id=request.user.id,
            threadflag__subscribed=True,
            last_update__gt=F('threadflag__last_read_date'))
        .order_by('-last_update'))

    threads_per_page = utils.get_config('threads_per_forum_page')
    paginator = utils.MappingPaginator(threads, threads_per_page)

    paginator.install_map_func(lambda t: utils.ThreadFascet(t, request))

    page = utils.page_by_request(paginator, request)

    ctx = {
        'threads': page
    }

    return render(request, 'user_cp.html', ctx)




def user_list(request):
    posters = Poster.objects.all().order_by('username')
    posters_per_page = 20
    pagniator = Paginator(posters, posters_per_page)

    page = utils.page_by_request(posters, posters_per_page)

    ctx = {
        'posters': page
    }

    return render(request, 'user_list.html', ctx)

def search(request):
    q = request.GET.get('q', None)

    if not q:
        return render(request, 'search_results.html', {})

    terms = ' & '.join(q.split(' '))
    qs = Post.objects.filter(content__tsmatch=terms).order_by('-created')

    posts_per_page = utils.get_config('general_items_per_page')

    paginator = Paginator(qs, posts_per_page)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'q': q,
        'posts': page
    }

    return render(request, 'search_results.html', ctx)

class UserProfile(utils.MethodSplitView):
    def GET(self, request, user_id):
        poster = get_object_or_404(Poster, pk=user_id)

        ctx = {
            'poster': poster,
            'bans': poster.bans.order_by('-start_date')
        }

        if poster.pk == request.user.pk:
            ctx['settings_form'] = self._base_settings_form(poster)
            ctx['avatar_form'] = self._base_avatar_form(poster)

        return render(request, 'user_profile.html', ctx)

    def POST(self, request, user_id):
        poster = get_object_or_404(Poster, pk=user_id)

        if poster.pk != request.user.pk:
            raise PermissionDenied()

        if request.POST.get('form_name') == 'SETTINGS':
            return self._process_settings_form(request, poster)
        elif request.POST.get('form_name') == 'AVATAR':
            return self._process_avatar_form(request, poster)
        else:
            return HttpResponseBadRequest('Invalid `form_name`')

    def _process_settings_form(self, request, poster):
        form = forms.UserSettingsForm(request.POST)

        if form.is_valid():
            form.save(poster)
            return HttpResponseRedirect(poster.get_url())

        else:
            ctx = {
                'poster': poster,
                'settings_form': form,
                'avatar_form': self._base_avatar_form(poster)
            }

            return render(request, 'user_profile.html', ctx)

    def _process_avatar_form(self, request, poster):
        form = forms.UserAvatarForm(request.POST, request.FILES)

        if form.is_valid():
            form.save(poster)
            poster.save()
            return HttpResponseRedirect(poster.get_url())

        else:
            ctx = {
                'poster': poster,
                'settings_form': self._base_settings_form(poster),
                'avatar_form': form
            }

            return render(request, 'user_profile.html', ctx)

    def _base_settings_form(self, poster):
        return forms.UserSettingsForm(initial={
            'email': poster.email,
            'allow_js': poster.allow_js,
            'allow_avatars': poster.allow_avatars,
            'allow_image_embed': poster.allow_image_embed,
            'auto_subscribe': poster.auto_subscribe,
            'timezone': poster.timezone,
            'posts_per_page': poster.posts_per_page})

    def _base_avatar_form(self, poster):
        return forms.UserAvatarForm()
        

class NewThread(utils.MethodSplitView):
    unbanned_required = True

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

class NewReply(utils.MethodSplitView):
    login_required = True
    unbanned_required = True

    def GET(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        form_initials = { 'thread': thread }
        author = request.user

        # Fetch BBCode for a quote in this response
        quoted_post_pk = request.GET.get('quote', None)
        if quoted_post_pk:
            try:
                quoted_post = Post.objects.get(pk=quoted_post_pk)
                form_initials['content'] = quoted_post.quote_content()

            except Post.DoesNotExist:
                pass

        form = forms.NewPostForm(author=author, initial=form_initials)
        
        ctx = {
            'thread': thread,
            'form': form
        }

        return render(request, 'new_post.html', ctx)

    def POST(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        author = request.user
        form = forms.NewPostForm(request.POST, author=author)

        if form.is_valid():
            post = form.save()

            if request.user.auto_subscribe == 1:
                thread.subscribe(request.user)
            
            return HttpResponseRedirect(post.get_url())

        else:
            ctx = {
                'thread': thread,
                'form': form
            }

            return render(request, 'new_post.html', ctx)

class EditPost(utils.MethodSplitView):
    unbanned_required = True
    
    def GET(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        form_initials = { 'content': post.content, 'post': post }

        if (not request.user == post.author) and (not request.user.is_staff):
            raise PermissionDenied()

        form = forms.EditPostForm(initial=form_initials)
        ctx = {
            'form': form,
            'post': post
        }

        return render(request, 'edit_post.html', ctx)

    def POST(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)

        if (not request.user == post.author) and (not request.user.is_staff):
            raise PermissionDenied()

        form = forms.EditPostForm(request.POST)

        if not form.is_valid():
            ctx = {
                'form': form,
                'post': post
            }

            return render(request, 'edit_post.html', ctx)

        form.save(editor=request.user)
        return HttpResponseRedirect(post.get_url())

def assume_identity(request, user_id):
    if not request.user.is_authenticated() or not request.user.is_admin:
        raise PermissionDenied()

    if not request.method == 'POST':
        return HttpResponseBadRequest('Method not supported.')

    target_user = get_object_or_404(Poster, pk=user_id)
    next_url = request.POST.get('next', '/')

    logout(request)
    login(request, target_user)

    return HttpResponseRedirect(next_url)


class GetQuote(utils.MethodSplitView):
    def GET(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        BBC = post.quote_content()

        return JsonResponse({
            'content': BBC
        })

class LoginUser(utils.MethodSplitView):
    def GET(self, request):
        form = forms.ISSAuthenticationForm()
        ctx = {'form': form}
        return render(request, 'login.html', ctx)

    def POST(self, request):
        logout(request)
        if request.POST:
            form = forms.ISSAuthenticationForm(data=request.POST, request=request)

            if form.is_valid():
                login(request, form.user_cache)
                next_url = request.POST.get('next', '/')
                return HttpResponseRedirect(next_url)

            else:
                ctx = {'form': form}
                return render(request, 'login.html', ctx)

class LogoutUser(utils.MethodSplitView):
    def POST(self, request):
        logout(request)

        next_url = request.POST.get('next', '/')
        return HttpResponseRedirect(next_url)

class RegisterUser(utils.MethodSplitView):
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


class ThankPost(utils.MethodSplitView):
    require_login = True
    unbanned_required = True

    def POST(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        thanks = Thanks(post=post, thanker=request.user, thankee=post.author)

        try:
            thanks.save()
        except IntegrityError:
            pass

        if request.is_ajax():
            return utils.render_mixed_mode(
                request,
                (('thanksBlock', 'thanks_block.html', {'post': post}),
                 ('postControls', 'post_controls.html', {'post': post})),
                additional={'status': 'SUCCESS'})
        else:
            return HttpResponseRedirect(post.get_url())

class UnthankPost(utils.MethodSplitView):
    require_login = True
    unbanned_required = True

    def POST(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        thanks = get_object_or_404(Thanks, post=post, thanker=request.user)

        thanks.delete()

        if request.is_ajax():
            return utils.render_mixed_mode(
                request,
                (('thanksBlock', 'thanks_block.html', {'post': post}),
                 ('postControls', 'post_controls.html', {'post': post})),
                additional={'status': 'SUCCESS'})

        return HttpResponseRedirect(post.get_url())

class SpamCanUser(utils.MethodSplitView):
    require_login = True
    require_staff = True

    def _get_threads(self, poster):
        threads = poster.thread_set.all()

        return threads

    def GET(self, request, poster_id):
        poster = get_object_or_404(Poster, pk=poster_id)
        next_page = request.GET.get(
            'next',
            reverse('user-profile', kwargs={'user_id':poster.pk}))
        form = forms.SpamCanUserForm(initial={
            'poster': poster,
            'next_page': next_page
        })
        threads = self._get_threads(poster)

        ctx = {
            'form': form,
            'next_page': next_page,
            'poster': poster,
            'threads': threads
        }

        return render(request, 'spam_can_user.html', ctx)

    @transaction.atomic
    def POST(self, request, poster_id):
        poster = get_object_or_404(Poster, pk=poster_id)
        threads = self._get_threads(poster)
        form = forms.SpamCanUserForm(request.POST)

        if form.is_valid():
            move_posts = poster.post_set.exclude(thread__in=threads)

            poster.is_active = False
            poster.is_staff = False
            poster.is_admin = False

            poster.save()

            threads.update(forum=form.cleaned_data['target_forum'])

            if move_posts.count():
                new_thread = Thread(
                    title='Deleted posts for: %s' % poster.username,
                    forum=form.cleaned_data['target_forum'],
                    author=poster)
                new_thread.save()

                move_posts.update(thread=new_thread)

            return HttpResponseRedirect(form.cleaned_data['next_page'])

        else:
            ctx = {
                'form': form,
                'next_page': form.cleaned_data['next_page'],
                'poster': poster,
                'threads': threads
            }

            return render(request, 'spam_can_user.html', ctx)

@cache_page(60 * 24 * 3, cache='db_cache')
def get_bc_embed_code(request):
    url = request.GET.get('url')

    if not url:
        return JsonResponse({
            'status': 'FAILURE',
            'reason': 'No url supplied'
        })

    try:
        embed_code = utils.bandcamp_markup_for_url(url)
    except utils.EmbeddingNotSupportedException:
        return JsonResponse({
            'status': 'FAILURE',
            'reason': 'Url is not embeddable'
        })
    except:
        return JsonResponse({
            'status': 'FAILURE',
            'reason': 'Unexpected failure'
        })
    else:
        return JsonResponse({
            'status': 'SUCCESS',
            'embedCode': embed_code
        })
    

class AutoAnonymize(utils.MethodSplitView):
    require_login = True

    def GET(self, request):
        return render(request, 'auto_anonymize.html', {})

    def POST(self, request):
        junk_user = Poster.get_or_create_junk_user()
        request.user.merge_into(junk_user)
        request.user.is_active = False
        request.user.save()
        logout(request)

        return HttpResponseRedirect(reverse('forum-index'))


class ReportPost(utils.MethodSplitView):
    require_login = True
    unbanned_required = True

    def pre_method_check(self, request, *args, **kwargs):
        if not request.user.can_report():
            raise PermissionDenied(
                'Your permission to report posts has been revoked.')

    def GET(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        form = forms.ReportPostForm(initial={'post': post})

        ctx = {
            'form': form,
            'post': post
        }

        return render(request, 'report_post.html', ctx)

    def POST(self, request, post_id):
        if not request.user.can_report():
            return HttpResponseForbidden('You can not report posts.')

        form = forms.ReportPostForm(request.POST)

        if form.is_valid():
            subject = '%s has reported a post by %s' % (
                request.user.username,
                form.cleaned_data['post'].author.username)

            content = render_to_string('pmt/report_post.bbc', form.cleaned_data,
                                       request=request)

            PrivateMessage.send_pm(
                Poster.get_or_create_system_user(),
                Poster.objects.filter(is_staff=True),
                subject,
                content)

            return HttpResponseRedirect(form.cleaned_data['post'].get_url())


        else:
            ctx = {
                'form': form,
                'post': get_object_or_404(Post, pk=post_id)
            }

            return render(request, 'report_post.html', ctx)

class BanPoster(utils.MethodSplitView):
    def pre_method_check(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('You are not authorized to ban posters.')

    def GET(self, request, user_id):
        poster = get_object_or_404(Poster, pk=user_id)
        form = forms.IssueBanForm(initial={'poster': poster})

        ctx = {
            'poster': poster,
            'form': form
        }

        return render(request, 'ban_poster.html', ctx)

    def POST(self, request, user_id):
        form = forms.IssueBanForm(request.POST)

        if form.is_valid():
            ban = Ban(
                subject=form.cleaned_data['poster'],
                given_by=request.user,
                end_date=timezone.now() + form.cleaned_data['duration'],
                reason=form.cleaned_data['reason'])

            ban.save()

            return HttpResponseRedirect(form.cleaned_data['poster'].get_url())

        else:
            ctx = {
                'form': form,
                'poster': get_object_or_404(Poster, pk=user_id)
            }

            return render(request, 'ban_poster.html', ctx)

class StaticPage(utils.MethodSplitView):
    def __init__(self, page_config):
        self.page_config = page_config
    
    def __call__(self, request):
        return render(request, 'static_page.html', self.page_config)

def humans(request):
    humans = utils.get_config('humans')

    s = '/* THOSE RESPONSIBLE */\n\n'

    for role, name, contact in humans:
        s += '%s: %s\nContact: %s\n\n' % (role, name, contact)

    top_posters = (Poster.objects.all()
        .annotate(num_posts=Count('post'))
        .order_by('num_posts'))[:3]

    if top_posters:
        s += '\n/* TOP SHITPOSTERS */\n\n'

        for poster in top_posters:
            s += 'Top Shitposter: %s\nContact: %s\nDamage Done: %d\n\n' % (
                poster.username, poster.get_url(), poster.num_posts)

    return HttpResponse(s, content_type='text/plain')
