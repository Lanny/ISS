from collections import defaultdict
import datetime

from django.contrib.auth import login, logout, authenticate, _get_backends
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction, connection
from django.db.models import Count, Max, F, Q
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden, HttpResponse)
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.template.defaultfilters import truncatechars
from django.views.decorators.cache import cache_control, cache_page

from ISS import utils, forms, iss_bbcode
from ISS.models import *
from ISS import models as iss_models
from ISS.hooks import HookManager

def _get_new_post_form(request):
    return utils.conditionally_captchatize(request, forms.NewPostForm)

@cache_control(max_age=60)
def forum_index(request):
    categories = Category.objects.all().order_by('priority', 'id')
    forums = Forum.objects.all().order_by('priority', 'id')

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
    threads = forum.thread_set.order_by('-stickied', '-last_update')
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
    posts = (thread.post_set
        .order_by('created')
        .select_related('author')
        .prefetch_related('thanks_set'))
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
            elif action == 'sticky-thread':
                return self._handle_sticky_thread(request, thread)
            elif action == 'lock-thread':
                return self._handle_lock_thread(request, thread)
            elif action == 'trash-thread':
                return self._handle_trash_thread(request, thread)
            elif action == 'off-topic-posts':
                return self._handle_off_topic_posts(request, thread)
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

    def _handle_sticky_thread(self, request, thread):
        if thread.stickied:
            thread.stickied = False
        else:
            thread.stickied = True
        thread.save()

        target = reverse('thread', kwargs={'thread_id': thread.pk})
        return HttpResponseRedirect(target)

    def _handle_lock_thread(self, request, thread):
        if thread.locked:
            thread.locked = False
        else:
            thread.locked = True
        thread.save()

        target = reverse('thread', kwargs={'thread_id': thread.pk})
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

    @transaction.atomic
    def _handle_off_topic_posts(self, request, thread):
        post_pks = request.POST.getlist('post', [])
        posts = [get_object_or_404(Post, pk=pk) for pk in post_pks]

        for post in posts:
            content = render_to_string(
                'pmt/off_topic_post.bbc',
                { 'post': post.content })

            iss_models.PrivateMessage.send_pm(
                iss_models.Poster.get_or_create_system_user(),
                [post.author],
                'Post marked as off-topic',
                content)
            post.delete()

        target = request.POST.get('next', None)
        target = target or reverse('thread', kwargs={'thread_id': thread.pk})
        return HttpResponseRedirect(target)

class UnsubscribeFromThread(utils.MethodSplitView):
    require_login = True

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
    effective_prefs = (LatestThreadsForumPreference
            .get_effective_preferences(
                request.user if request.user.is_authenticated() else None))

    excluded_forums = [
        fpk for fpk, include in effective_prefs.items() if not include]

    threads = (Thread.objects.all()
        .filter(~Q(forum_id__in=excluded_forums))
        .order_by('-last_update')
        .select_related('author'))

    threads_per_page = utils.get_config('threads_per_forum_page')
    paginator = utils.MappingPaginator(threads, threads_per_page)

    paginator.install_map_func(lambda t: utils.ThreadFascet(t, request))
    page = utils.page_by_request(paginator, request)

    # We can apparently do aggregate queries faster than the ORM, so do that.
    # This is ugly but this is one of the highest traffic pages in the project
    # and we can make a _big_ perf difference (as in an order of magnitude) by
    # doing these queries together like this.
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT post.thread_id, COUNT(*) FROM "ISS_post" AS post
                WHERE post.thread_id = ANY(%s)
                GROUP BY post.thread_id
        """, ([tf._thread.pk for tf in page],))
        counts = dict(cursor.fetchall())

        for tf in page:
            tf._thread.post_count = counts[tf._thread.pk]


        if request.user.is_authenticated():
            ppk = request.user.pk
            flags = ThreadFlag.objects.raw("""
                SELECT tf.*
                    FROM "ISS_thread" AS thread
                    JOIN "ISS_threadflag" AS tf ON
                        tf.thread_id = thread.id
                        AND tf.poster_id = %s
                WHERE thread.id = ANY(%s)
            """, (ppk, [tf._thread.pk for tf in page]))
            fd = dict([(flag.thread_id, flag) for flag in flags])
            for tf in page:
                if tf._thread.pk in fd:
                    tf._thread._flag_cache[ppk] = fd[tf._thread.pk]

    ctx = {
        'rel_page': page,
        'threads': page
    }

    return render(request, 'latest_threads.html', ctx)


class UpdateLatestThreadsPreferences(utils.MethodSplitView):
    require_login = True

    def GET(self, request):
        form = forms.LatestThreadsPreferencesForm(poster=request.user)
        ctx = { 'form': form }
        return render(request, 'update_latest_threads_preferences.html', ctx)

    def POST(self, request):
        form = forms.LatestThreadsPreferencesForm(request.POST)

        if form.is_valid():
            old_prefs = (LatestThreadsForumPreference
                .get_effective_preferences(poster=request.user))
            new_prefs = form.get_effective_preferences()
            diff_keys = []

            for fpk, new_pref in new_prefs.items():
                if new_pref != old_prefs[fpk]:
                    diff_keys.append(fpk)

            for fpk in diff_keys:
                pref, created = (LatestThreadsForumPreference
                    .objects
                    .get_or_create(
                        poster=request.user,
                        forum_id=fpk,
                        defaults={'include': new_prefs[fpk]}))

                if not created:
                    pref.include = new_prefs[fpk]
                    pref.save()

            return HttpResponseRedirect(reverse('latest-threads'))

        else:
            ctx = { 'form': form }
            return render(
                request,
                'update_latest_threads_preferences.html',
                ctx)

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

class MarkSubsriptionsRead(utils.MethodSplitView):
    require_login = True

    def POST(self, request):
        (request
            .user
            .threadflag_set
            .filter(subscribed=True)
            .update(last_read_date=timezone.now()))
        return HttpResponseRedirect(reverse('usercp'))

def search(request):
    q = request.GET.get('q', None)

    # Special case for no query param, user is probably landing here
    # without having filled out a query yet.
    if not q:
        return render(request, 'search_results.html', {
            'form': forms.SearchForm()
        })

    else:
        form = forms.SearchForm(request.GET)
        if form.is_valid():
            d = form.cleaned_data
            terms = ' & '.join(d['q'].split(' '))

            model = None
            filter_q = {}

            if d['search_type'] == 'threads':
                model = Thread
                filter_q['title__tsmatch'] =  terms
                if d['forum']: filter_q['forum__in'] = d['forum']
            else:
                model = Post
                filter_q['content__tsmatch'] = terms
                if d['forum']: filter_q['thread__forum__in'] = d['forum']

            if d['author']:
                filter_q['author__in'] = d['author']

            qs = model.objects.filter(**filter_q).order_by('-created')


            items_per_page = utils.get_config('general_items_per_page')
            paginator = Paginator(qs, items_per_page)
            page = utils.page_by_request(paginator, request)

            ctx = {
                'rel_page': page,
                'page': page,
                'form': form,
                'q': d['q']
            }
        else:
            ctx = {
                'form': form
            }

        return render(request, 'search_results.html', ctx)


class NewThread(utils.MethodSplitView):
    require_login = True
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
    require_login = True
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
    require_login = True

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

    @RateLimitedAccess.rate_limit('login', 10, datetime.timedelta(hours=1))
    def POST(self, request):
        logout(request)
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
            max_subject_len = (PrivateMessage._meta
                .get_field('subject')
                .max_length)
            subject = '%s has reported a post by %s' % (
                truncatechars(request.user.username, 75),
                truncatechars(form.cleaned_data['post'].author.username, 75),
            )
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

