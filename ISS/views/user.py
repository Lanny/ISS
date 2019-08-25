import uuid
from smtplib import SMTPRecipientsRefused
from datetime import timedelta

from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.db import transaction
from django.db.models import Count
from django.forms import ValidationError
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden, HttpResponse)

from ISS import utils, forms
from ISS.models import *
from ISS.hooks import HookManager

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
            'theme': poster.theme,
            'posts_per_page': poster.posts_per_page,
            'pgp_key': poster.pgp_key
        })

    def _base_avatar_form(self, poster):
        return forms.UserAvatarForm()
        

class InitiatePasswordRecovery(utils.MethodSplitView):
    def GET(self, request):
        form = forms.InitiatePasswordRecoveryForm()
        ctx = {'form': form}
        return render(request, 'initiate_password_recovery.html', ctx)

    def POST(self, request):
        form = forms.InitiatePasswordRecoveryForm(request.POST)

        if form.is_valid():
            normalized = Poster.normalize_username(
                form.cleaned_data['username'])
            user = Poster.objects.get(normalized_username=normalized)
            user.recovery_code = str(uuid.uuid4())
            user.recovery_expiration = (
                timezone.now() + timedelta(days=1))
            user.save()

            forum_name = utils.get_config('forum_name')
            ctx = {
                'forum_name': forum_name,
                'url': (utils.reverse_absolute('recovery-reset') +
                    '?code=' + user.recovery_code)
            }

            send_mail(
                'Password Recovery for %s' % forum_name,
                render_to_string('email/password_recovery.txt', ctx),
                settings.EMAIL_HOST_USER,
                [user.email])

            return render(request, 'generic_message.html', {
                'page_title': 'Recovery Email Sent',
                'heading': 'Recovery Email Sent',
                'message': ('You should receive an email containing further '
                            'instructions on how to reset your password at the '
                            'address you submitted shortly. If you don\'t see '
                            'it please check your spam folder.')
            })
        else:
            ctx = { 'form': form }
            return render(request, 'initiate_password_recovery.html', ctx)

class ExecutePasswordRecovery(utils.MethodSplitView):
    def pre_method_check(self, request, *args, **kwargs):
        code = request.GET.get('code', None) or request.POST.get('code', None)
        target_user_qs = Poster.objects.filter(recovery_code=code)

        if (not code or
                not target_user_qs.count() == 1 or
                timezone.now() > target_user_qs[0].recovery_expiration):
            return render(request, 'generic_message.html', {
                'page_title': 'Invalid Recovery Code',
                'heading': 'Invalid Recovery Code',
                'message': ('The recovery code specified is either invalid or '
                            'has expired. Please re-request a recovery code to '
                            'proceed with password reset.')
                },
                status=404)


    def GET(self, request):
        form = forms.ExecutePasswordRecoveryForm(initial={
            'code': request.GET.get('code', '')
        })
        ctx = {'form': form}
        return render(request, 'execute_password_recovery.html', ctx)

    def POST(self, request):
        form = forms.ExecutePasswordRecoveryForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']
            user = Poster.objects.get(recovery_code=code)
            user.recovery_code = None
            user.set_password(form.cleaned_data['password'])
            user.save()

            return render(request, 'generic_message.html', {
                'page_title': 'Recovery Complete',
                'heading': 'Recovery Complete',
                'message': ('The password for %s has been successfully '
                            'updated, you may log into that account using it '
                            'now') % (user.username,)
            })
            

        else:
            ctx = { 'form': form }
            return render(request, 'execute_password_recovery.html', ctx)
    

class RegisterUser(utils.MethodSplitView):
    def pre_method_check(self, request, *args, **kwargs):
        if not utils.get_config('enable_registration'):
            message = ('Registration is temporarily closed. Check back later '
                       'to register a new account. If you think this is in '
                       'error, please contact the administrator.')

            if utils.get_config('enable_invites'):
                url = reverse('register-with-code')
                message += (' If you have a registration code, you may use it '
                            'by clicking [url="%s"]here[/url].') % url

            return render(request, 'generic_message.html', {
                'page_title': 'Registration Closed',
                'heading': 'Registration Closed',
                'message': message
            })

    def _form_error(self, request, form):
        ctx = { 'form': form }
        return render(request, 'register.html', ctx)

    def _create_poster(self, form):
        poster = form.save()
        poster.is_active = False
        poster.save()

        return poster

    def _send_verificaiton_email(self, poster):
        forum_name = utils.get_config('forum_name')
        email_address = poster.email

        verification_url = '%s?code=%s' % (
            utils.reverse_absolute('verify-email'),
            poster.email_verification_code)
        
        ctx = {
            'forum_name': forum_name,
            'username': poster.username,
            'email_address': email_address,
            'verification_url': verification_url,
        }

        send_mail(
            'Account Verification for %s' % forum_name,
            render_to_string('email/account_verification.txt', ctx),
            settings.EMAIL_HOST_USER,
            [email_address])

    def GET(self, request):
        form = forms.RegistrationForm()
        ctx = {'form': form}
        return render(request, 'register.html', ctx)

    def POST(self, request):
        form = forms.RegistrationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    poster = self._create_poster(form)
                    self._send_verificaiton_email(poster)

            except SMTPRecipientsRefused:
                error = ValidationError(
                    'Unable to send verification email to: %(email)s.',
                    params={ 'email': form.cleaned_data['email'] },
                    code="SMTP_ERROR")
                form.add_error('email', error)
                return self._form_error(request, form)

            forum_name = utils.get_config('forum_name')
            email_address = poster.email
            message = (
                'Thank you for registering with %s. You\'ll need to verify '
                'your email address before logging in. We\'ve send an email '
                'to %s. Please check that address and follow the instructions '
                'in the email. Note that it may take a few minutes for the '
                'email to arrive. If you don\'t receive an email check your '
                'spam folder.'
            ) % (forum_name, email_address)

            return render(request, 'generic_message.html', {
                'page_title': 'Regristration Successful',
                'heading': 'Regristration Successful',
                'message': message
            })

        else:
            return self._form_error(request, form)

class VerifyEmail(utils.MethodSplitView):
    def _error_out(self, request):
        message = ('The verification code is either invalid or already '
            'used. Please check the code sent in the verification email.')

        return render(
            request,
            'generic_message.html',
            {
                'page_title': 'Error',
                'heading': 'Verification Code Invalid',
                'message': message
            },
            status=404)

    def GET(self, request):
        try:
            code = uuid.UUID(request.GET.get('code', ''))
        except ValueError:
            return self._error_out(request)

        try :
            poster = Poster.objects.get(email_verification_code=code)
        except Poster.DoesNotExist:
            return self._error_out(request)

        if poster.is_active:
            return self._error_out(request)

        poster.is_active = True
        poster.save()

        message = ('You\'ve successfully verified your account, welcome to '
            '%s. You can now [url="%s"]log in[/url] to your account.')
        message = message % (utils.get_config('forum_name'), reverse('login'))

        return render(request, 'generic_message.html', {
            'page_title': 'Verification Successful',
            'heading': 'Verification Successful',
            'message': message
        })

class RegisterUserWithCode(utils.MethodSplitView):
    def GET(self, request):
        form = forms.InviteRegistrationFrom(initial={
            'registration_code': request.GET.get('code', '')
        })
        ctx = {'form': form}
        return render(request, 'register.html', ctx)

    def POST(self, request):
        form = forms.InviteRegistrationFrom(request.POST)

        if form.is_valid():
            poster = form.save()

            poster = authenticate(username = form.cleaned_data['username'],
                                  password = form.cleaned_data['password1'])
            login(request, poster)
            return HttpResponseRedirect('/')

        else:
            ctx = { 'form': form }
            return render(request, 'register.html', ctx)

class GenerateInvite(utils.MethodSplitView):
    login_required = True
    unbanned_requried = True
    
    def pre_method_check(self, request, *args, **kwargs):
        acl = AccessControlList.get_acl('CREATE_INVITE')

        if not acl.is_poster_authorized(request.user):
            raise PermissionDenied('Not allowed to invite users')

    def GET(self, request):
        return render(request, 'generate_invite.html', {})

    def POST(self, request):
        reg_code = RegistrationCode(generated_by=request.user)
        reg_code.save()
        url = reverse('view-generated-invite') + '?code=%s' % reg_code.code
        return HttpResponseRedirect(url)

def user_index(request):
    posters = Poster.objects.all().order_by('id')
    posters_per_page = utils.get_config('general_items_per_page')

    paginator = Paginator(posters, posters_per_page)
    page = utils.page_by_request(paginator, request)

    ctx = {
        'rel_page': page,
        'posters': page,
        'members_action_form': forms.MembersListActionsForm()
    }

    return render(request, 'user_index.html', ctx)

class MembersListActions(utils.MethodSplitView):

    def POST(self, request):
        form = forms.MembersListActionsForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'sort-by-id':
                return self._sort_by_username(request)
            elif action == 'sort-by-username':
                return self._sort_by_username(request)
            elif action == 'sort-by-post-count':
                return self._sort_by_post_count(request)
            else:
                raise Exception('Unexpected action.')
        else:
            return HttpResponseBadRequest('Invalid form.')

    @transaction.atomic
    def _sort_by_id(self, request):
        return HttpResponseBadRequest('Invalid form.')

    @transaction.atomic
    def _sort_by_username(self, request):
        return HttpResponseBadRequest('Invalid form.')

    @transaction.atomic
    def _sort_by_post_count(self, request):
        return HttpResponseBadRequest('Invalid form.')

def view_generated_invite(request):
    reg_code = get_object_or_404(RegistrationCode, code=request.GET.get('code'))
    ctx = { 'reg_code': reg_code }
    return render(request, 'view_generated_invite.html', ctx)

def user_fuzzy_search(request):
    query = request.GET.get('q', '')
    nquery = Poster.normalize_username(query)
    matches = (Poster.objects
        .filter(normalized_username__contains=nquery, is_active=True)
        .annotate(post_count=Count('post'))
        .order_by('-post_count'))[:7]
    response_users = []

    for match in matches:
        response_users.append({
            'name': match.username,
            'pk': match.pk
        })

    return JsonResponse({
        'results': response_users,
        'resultType': 'user'
    })
