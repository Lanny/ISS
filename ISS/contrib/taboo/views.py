from django.db.models import Count
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.utils import timezone
from django.shortcuts import render, get_object_or_404

from ISS import models as iss_models
from ISS.utils import MethodSplitView
from models import *
from apps import TabooConfig

EXT = TabooConfig.name

def is_eligible(user):
    min_posts = iss_utils.get_ext_config(EXT, 'min_posts_to_reg')
    min_age = iss_utils.get_ext_config(EXT, 'min_age_to_reg')

    if (timezone.now() - user.date_joined) < min_age:
        return False

    if user.post_set.count() < min_posts:
        return False

    try:
        profile = TabooProfile.objects.get(poster=user)

        cooldown = iss_utils.get_ext_config(EXT, 'reregister_cooldown')
        if timezone.now() - profile.last_registration < cooldown:
            return False
        else:
            return True
    except TabooProfile.DoesNotExist:
        return True

class Status(MethodSplitView):
    require_login = True
    unbanned_required = True

    def GET(self, request):
        return render(request, 'taboo/status.html', {
            'eligible': is_eligible(request.user)
        })

class Register(MethodSplitView):
    require_login = True
    unbanned_required = True

    def POST(self, request):
        if not is_eligible(request.user):
            return HttpResponseBadRequest('Not eligible.')

        # Rectify violations here because cron jobs are nasty
        TabooViolationRecord.rectify_all_usertitles()

        profile = None
        try:
            profile = TabooProfile.objects.get(poster=request.user)
        except TabooProfile.DoesNotExist:
            profile = TabooProfile(poster=request.user)

        profile.active = True
        profile.last_registration = timezone.now()
        profile.mark = None
        profile.save()

        return HttpResponseRedirect(reverse('taboo-status'))

class Unregister(MethodSplitView):
    require_login = True
    unbanned_required = True

    def POST(self, request):
        profile = get_object_or_404(TabooProfile, poster=request.user)
        profile.active = False
        profile.save()

        those_marking = TabooProfile.objects.filter(mark=profile.poster)
        for prof in those_marking:
            prof.mark = None
            prof.save()

        # Rectify violations here because cron jobs are nasty
        TabooViolationRecord.rectify_all_usertitles()

        return HttpResponseRedirect(reverse('taboo-status'))

def leader_board(request):
    players = (iss_models.Poster
        .objects
        .all()
        .annotate(victories=Count('taboo_successes'))
        .annotate(losses=Count('taboo_failures'))
        .filter(victories__gt=0)
        .order_by('victories'))


    return render(request, 'taboo/leader_board.html', {
        'players': players
    })
