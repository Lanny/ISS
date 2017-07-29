import uuid
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden, HttpResponse)


from ISS import utils, forms
from ISS.models import *

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

            ctx = {
                'url': (utils.get_config('forum_domain') +
                        reverse('recovery-reset') +
                        '?code=' + user.recovery_code)
            }

            send_mail(
                'Password Recovery for %s' % utils.get_config('forum_name'),
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
            return render(request, 'generic_message.html', {
                'page_title': 'Registration Closed',
                'heading': 'Registration Closed',
                'message': ('Registration is temporarily closed. Check back '
                            'later to register a new account. If you think '
                            'this is in error, please contact the '
                            'administrator.')
            })

    def GET(self, request):
        form = forms.RegistrationForm()
        ctx = {'form': form}
        return render(request, 'register.html', ctx)

    def POST(self, request):
        form = forms.RegistrationForm(request.POST)

        if form.is_valid():
            poster = form.save()

            poster = authenticate(username = form.cleaned_data['username'],
                                  password = form.cleaned_data['password1'])
            login(request, poster)
            return HttpResponseRedirect('/')

        else:
            ctx = { 'form': form }
            return render(request, 'register.html', ctx)

class RegisterUserWithCode(utils.MethodSplitView):
    def GET(self, request):
        form = forms.InviteRegistrationFrom()
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


