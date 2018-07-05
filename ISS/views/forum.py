from collections import defaultdict

from django.contrib.auth import login, logout, authenticate, _get_backends
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, F, Q
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden, HttpResponse)
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control, cache_page

from ISS import utils, forms, iss_bbcode
from ISS.models import *
from ISS.hooks import HookManager

def _get_new_post_form(request):
    return utils.conditionally_captchatize(request, forms.NewPostForm)

@cache_control(max_age=60)
def forum_index(request):
    categories = Category.objects.all().order_by('priority')
    forums = Forum.objects.all().order_by('priority')

    # Start: optimization to prefetch additional stats and flags for forums in
    # one go as opposed to querying per-forum
    forums_w_posts = forums.annotate(post_count=Count('thread__post'))
    forums_post_map = dict([(f.pk, f.post_count) for f in forums_w_posts])
    forums = list(forums.annotate(thread_count=Count('thread')))

    for forum in forums:
        forum.post_count = forums_post_map[forum.pk]

    if request.user.is_authenticated():
        d = dict([(f.pk, f) for f in forums])
        flags = ForumFlag.objects.filter(poster=request.user, forum__in=forums)

        for flag in flags:
            d[flag.forum_id]._flag_cache = flag
    # End

    ctx = {
        'categories': categories,
        'forums_by_category': defaultdict(list)
    }

    for forum in forums:
        fasceted = utils.ForumFascet(forum, request)
        ctx['forums_by_category'][forum.category_id].append(fasceted)

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
        'rel_page': page,
        'forum': forum,
        'threads': page,
        'can_start_thread': forum.create_thread_pack.check_request(request)
    }

    if request.user.is_authenticated():
        forum.mark_read(request.user)

    return render(request, 'thread_index.html', ctx)

def thread(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    posts = thread.post_set.order_by('created').select_related('author')
    page = utils.get_posts_page(posts, request)
    reply_form = _get_new_post_form(request)(author=request.user,
                                             initial={ 'thread': thread })

    ctx = {
        'rel_page': page,
        'thread': thread,
        'posts': page,
        'reply_form': reply_form,
        'thread_action_form': forms.ThreadActionForm()
    }

    response = render(request, 'thread.html', ctx)

    # Update thread flag
    if request.user.is_authenticated():
        thread.mark_read(request.user, page[-1])

        if request.user.auto_subscribe == 2:
            thread.subscribe(request.user)

    return response

class ThreadActions(utils.MethodSplitView):
    staff_required = True
    unbanned_required = True

    def POST(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        form = forms.ThreadActionForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'edit-thread':
                return self._handle_edit_thread(request, thread)
            elif action == 'delete-posts':
                return self._handle_delete_posts(request, thread)
            elif action == 'trash-thread':
                return self._handle_trash_thread(request, thread)
            elif re.match('move-to-(\d+)', action):
                return self._handle_move_thread(request, thread, action)
            else:
                raise Exception('Unexpected action.')
        else:
            return HttpResponseBadRequest('Invalid form.')

    def _handle_edit_thread(self, request, thread):
        target = reverse('admin:ISS_thread_change',
                         args=[thread.pk])
        return HttpResponseRedirect(target)

    def _handle_trash_thread(self, request, thread):
        trash_forums = Forum.objects.filter(is_trash=True)

        if trash_forums:
            thread.forum = trash_forums[0]
            thread.save()

        target = request.POST.get('next', None)
        target = target or reverse('thread', kwargs={'thread_id': thread.pk})
        return HttpResponseRedirect(target)

    def _handle_move_thread(self, request, thread, action):
        fid = int(re.match('move-to-(\d+)', action).group(1))
        thread.forum = Forum.objects.get(pk=fid)
        thread.save()

        target = reverse('thread', kwargs={'thread_id': thread.pk})
        return HttpResponseRedirect(target)

    @transaction.atomic
    def _handle_delete_posts(self, request, thread):
        post_pks = request.POST.getlist('post', [])
        posts = [get_object_or_404(Post, pk=pk) for pk in post_pks]

        for post in posts:
            post.delete()

        target = request.POST.get('next', None)
        target = target or reverse('thread', kwargs={'thread_id': thread.pk})
        return HttpResponseRedirect(target)

class UnsubscribeFromThread(utils.MethodSplitView):
    login_required = True

    def POST(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        thread.unsubscribe(request.user)

        return HttpResponseRedirect(request.POST.get('next', '/'))

def redirect_to_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    thread = post.thread
    predecessors = (thread.get_posts_in_thread_order()
            .filter(created__lt=post.created)
            .count())
    page_num = predecessors / utils.get_posts_per_page(request.user)
    target_url = thread.get_url() + '?p=%d#post-%d' % (page_num + 1, post.pk)

    return HttpResponseRedirect(target_url)

def threads_by_user(request, user_id):
    poster = get_object_or_404(Poster, pk=user_id)
    threads = Thread.objects.filter(author=poster).order_by('-created')
    threads_per_page = utils.get_config('general_items_per_page')
    paginator = Paginator(threads, threads_per_page)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'rel_page': page,
        'poster': poster,
        'threads': page
    }

    return render(request, 'threads_started.html', ctx)

def posts_by_user(request, user_id):
    poster = get_object_or_404(Poster, pk=user_id)
    posts = (poster.post_set
        .order_by('-created')
        .select_related('thread'))
    posts_per_page = utils.get_config('general_items_per_page')
    paginator = Paginator(posts, posts_per_page)

    page = utils.page_by_request(paginator, request)

    ctx = {
        'rel_page': page,
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
        'rel_page': page,
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
        'rel_page': page,
        'poster': poster,
        'posts': page
    }

    return render(request, 'posts_thanked.html', ctx)


@cache_control(no_cache=True, max_age=0, must_revalidate=True, no_store=True)
def latest_threads(request):
    effective_prefs = {}
    trash_forums = []

    for forum in Forum.objects.all():
        effective_prefs[forum.pk] = forum.include_in_lastest_threads 
        if forum.is_trash: trash_forums.append(forum.pk)

    if request.user.is_authenticated():
        prefs = LatestThreadsForumPreference.objects.filter(poster=request.user)
        for pref in prefs:
            effective_prefs[pref.forum_id] = pref.include

    for fpk in trash_forums:
        effective_prefs[fpk] = False


    print effective_prefs
    excluded_forums = [
        fpk for fpk, include in effective_prefs.items() if not include]
    print excluded_forums

    threads = (Thread.objects.all()
        .filter(~Q(forum_id__in=excluded_forums))
        .order_by('-last_update'))

    threads_per_page = utils.get_config('threads_per_forum_page')
    paginator = utils.MappingPaginator(threads, threads_per_page)

    paginator.install_map_func(lambda t: utils.ThreadFascet(t, request))

    page = utils.page_by_request(paginator, request)

    ctx = {
        'rel_page': page,
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
        'rel_page': page,
        'threads': page
    }

    return render(request, 'user_cp.html', ctx)

def user_list(request):
    posters = Poster.objects.all().order_by('username')
    posters_per_page = 20
    pagniator = Paginator(posters, posters_per_page)

    page = utils.page_by_request(posters, posters_per_page)

    ctx = {
        'rel_page': page,
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
        'rel_page': page,
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

        ip_acl = AccessControlList.get_acl('VIEW_IPS')
        if ip_acl.is_poster_authorized(request.user):
            ip_distr = (poster.post_set
                .values('posted_from')
                .annotate(num_posts=Count('id'))
                .order_by('-num_posts'))

            ctx['ip_distr'] = ip_distr[:10]
            ctx['ip_distr_remaining'] = max(ip_distr.count() - 10, 0)

        HookManager.add_ctx_for_hook(ctx, 'user_profile_stats', poster)

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

            HookManager.add_ctx_for_hook(ctx, 'user_profile_stats', poster)

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

            HookManager.add_ctx_for_hook(ctx, 'user_profile_stats', poster)

            return render(request, 'user_profile.html', ctx)

    def _base_settings_form(self, poster):
        return forms.UserSettingsForm(initial={
            'email': poster.email,
            'allow_js': poster.allow_js,
            'allow_avatars': poster.allow_avatars,
            'allow_image_embed': poster.allow_image_embed,
            'allow_video_embed': poster.allow_video_embed,
            'enable_editor_buttons': poster.enable_editor_buttons,
            'enable_tripphrase': not (poster.tripphrase == None),
            'auto_subscribe': poster.auto_subscribe,
            'timezone': poster.timezone,
            'posts_per_page': poster.posts_per_page })

    def _base_avatar_form(self, poster):
        return forms.UserAvatarForm()
        

class NewThread(utils.MethodSplitView):
    login_required = True
    unbanned_required = True

    def _get_form(self, request):
        return utils.conditionally_captchatize(request, forms.NewThreadForm)

    def GET(self, request, forum_id):
        forum = get_object_or_404(Forum, pk=forum_id)
        form = self._get_form(request)(initial={ 'forum': forum },
                                       author=request.user)

        forum.create_thread_pack.validate_request(request)
        
        ctx = {
            'forum': forum,
            'form': form
        }

        return render(request, 'new_thread.html', ctx)

    def POST(self, request, forum_id):
        forum = get_object_or_404(Forum, pk=forum_id)
        form = self._get_form(request)(request.POST, author=request.user)

        forum.create_thread_pack.validate_request(request)

        if form.is_valid():
            ip_addr = request.META.get(
                    utils.get_config('client_ip_field'), None)

            thread = form.save(request.user, ip_addr)

            if request.user.auto_subscribe >= 1:
                thread.subscribe(request.user)

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

    def _get_form(self, request):
        return _get_new_post_form(request)

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

        form = self._get_form(request)(author=author, initial=form_initials)
        
        ctx = {
            'thread': thread,
            'form': form
        }

        return render(request, 'new_post.html', ctx)

    def POST(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        author = request.user
        form = self._get_form(request)(request.POST, author=author)

        if form.is_valid():
            post = form.get_post()
            post.posted_from = request.META.get(
                    utils.get_config('client_ip_field'), None)
            post.save()

            if request.user.auto_subscribe == 1:
                thread.subscribe(request.user)
            
            return HttpResponseRedirect(post.get_url())

        else:
            ctx = {
                'thread': thread,
                'form': form
            }

            return render(request, 'new_post.html', ctx)

class PreviewPost(utils.MethodSplitView):
    login_required = True

    def POST(self, request, action):
        struct_form = forms.StructuralPreviewPostForm(request.POST)

        if struct_form.is_valid():
            content = request.POST.get('content', '')
            form_action, secondary_form = self.get_secondary_form(
                struct_form, request, content)

            preview_action = reverse('preview-post', kwargs={'action': action})
            ctx = {
                'form_action': form_action,
                'form': secondary_form,
                'preview_action': preview_action,
                'action': action,
                'content': content
            }

            return render(request, 'preview_post.html', ctx)

        else:
            return HttpResponseBadRequest('Invalid form.')


    def get_secondary_form(self, preview_form, request, content):
        action = preview_form.cleaned_data['preview_action']

        form = None
        form_action = None

        if action == 'new-reply':
            Form = utils.conditionally_captchatize(request, forms.NewPostForm)
            thread = preview_form.cleaned_data['thread']
            form_action = reverse('new-reply', kwargs={'thread_id': thread.pk})
            form = Form(request.POST, author=request.user)

        elif action == 'edit-post':
            post = preview_form.cleaned_data['post'] 
            form_action = reverse('edit-post', kwargs={'post_id': post.pk})
            form = forms.EditPostForm(request.POST)

        elif action == 'new-thread':
            forum = preview_form.cleaned_data['forum'] 
            form_action = reverse('new-thread', kwargs={'forum_id': forum.pk})
            Form = utils.conditionally_captchatize(request, forms.NewThreadForm)
            form = Form(request.POST, author=request.user)

        elif action == 'compose-pm':
            form_action = reverse('compose-pm')
            form = forms.NewPrivateMessageForm(request.POST, author=request.user)

        return (form_action, form)

class RenderBBCode(utils.MethodSplitView):
    def POST(self, request):
        form = forms.RenderBBCodeForm(request.POST)

        if form.is_valid():
            ctx = { 'content': request.POST['content'] }

            return utils.render_mixed_mode(
                request,
                (('postPreview', 'post_preview_block.html', ctx),),
                additional={'status': 'SUCCESS'})
        else:
            return JsonResponse({
                'status': 'INVALID_FORM',
                'errors': form.errors
            })

class EditPost(utils.MethodSplitView):
    unbanned_required = True

    def pre_method_check(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        if not post.can_be_edited_by(request.user):
            raise PermissionDenied()
    
    def GET(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        form_initials = { 'content': post.content, 'post': post }
        form = forms.EditPostForm(initial=form_initials)
        ctx = {
            'form': form,
            'post': post
        }

        return render(request, 'edit_post.html', ctx)

    def POST(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        form = forms.EditPostForm(request.POST)

        if not form.is_valid():
            ctx = {
                'form': form,
                'post': post
            }

            return render(request, 'edit_post.html', ctx)

        ip_addr = request.META.get(utils.get_config('client_ip_field'), None)
        form.save(editor=request.user, editor_ip=ip_addr)
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
        form = forms.ISSAuthenticationForm(autofocus=True)
        ctx = {'form': form}
        return render(request, 'login.html', ctx)

    def POST(self, request):
        logout(request)
        if request.POST:
            form = forms.ISSAuthenticationForm(autofocus=True,
                                               data=request.POST,
                                               request=request)

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

class ThankPost(utils.MethodSplitView):
    require_login = True
    unbanned_required = True

    def POST(self, request, post_id):
        min_posts = utils.get_config('initial_account_period_total')
        if request.user.post_set.count() < min_posts:
            raise PermissionDenied('Not enough posts to thank.')

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
    staff_required = True

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

            Ban.objects.create(given_by=request.user,
                               subject=poster,
                               reason="spam ban")

            poster.save()

            threads.update(forum=form.cleaned_data['target_forum'])

            if move_posts.count():
                new_thread = Thread(
                    title='Deleted posts for: %s' % poster.username,
                    forum=form.cleaned_data['target_forum'],
                    author=poster)
                new_thread.save()

                for post in move_posts:
                    post.move_to_thread(new_thread)

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
    except iss_bbcode.EmbeddingNotSupportedException:
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

    def pre_method_check(self, request, *args, **kwargs):
        if not request.user.can_auto_anonymize():
            raise PermissionDenied('Account not old enough.')

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

def view_static_page(request, page_id):
    page = get_object_or_404(StaticPage, page_id=page_id)
    ctx = {
        'page_title': page.page_title,
        'content': page.content
    }
    return render(request, 'static_page.html', ctx)

def humans(request):
    humans = utils.get_config('humans')

    s = '/* THOSE RESPONSIBLE */\n\n'

    for role, name, contact in humans:
        s += '%s: %s\nContact: %s\n\n' % (role, name, contact)

    top_posters = (Poster.objects.all()
        .annotate(num_posts=Count('post'))
        .order_by('-num_posts'))[:3]

    if top_posters:
        s += '\n/* TOP SHITPOSTERS */\n\n'

        for poster in top_posters:
            s += 'Top Shitposter: %s\nContact: %s\nDamage Done: %d\n\n' % (
                poster.username, poster.get_url(), poster.num_posts)

    return HttpResponse(s, content_type='text/plain')

def robots(request):
    robots = [
        '# ISS robots.txt, please crawl responsibly. We ask that you keep ',
        '# crawling to a few (as in less than 4) requests per second. Fully ',
        '# recursive crawling is acceptable under the condition that the ',
        '# disallowed urls are ignored for ranking operations as we maintain ',
        '# content the owners explicitly disavow (spam) for legal reasons ',
        '# under some of these urls.',
        '#',
        '# Please note that paginated post lists like those matching ',
        '# /forum/\d+/ are sorted in reverse cronological order and their ',
        '# content is highly dynamic while most other paginated lists are ',
        '# append-only and will remain fairly stable.',
        'User-agent: *',
        'Disallow: /pms/',
        'Disallow: /api/',
        'Disallow: /embed/',
        'Disallow: /search',
        'Disallow: /search/',
    ]

    for forum in Forum.objects.filter(is_trash=True):
        url = reverse('thread-index', args=(forum.pk,))
        robots.append('Disallow: %s' % url)

    return HttpResponse('\n'.join(robots), content_type='text/plain')

@cache_page(60 * 24 * 7)
@cache_control(max_age=60*24)
def smilies_css(request):
    return render(request, 'smilies.css', content_type='text/css')


