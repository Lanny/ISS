from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone
from django import forms

from ISS import utils
from .core_models import Forum, Poster, Thread
from .admin_models import IPBan

class LatestThreadsForumPreference(models.Model):
    class Meta:
        unique_together = ('poster', 'forum')

    poster = models.ForeignKey(Poster, on_delete=models.CASCADE)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)

    include = models.BooleanField(null=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def get_poster_preferences(cls, poster):
        poster_prefs = {}

        prefs = LatestThreadsForumPreference.objects.filter(poster=poster)
        for pref in prefs:
            poster_prefs[pref.forum_id] = pref.include

        return poster_prefs

    @classmethod
    def get_effective_preferences(cls, poster=None):
        effective_prefs = {}
        trash_forums = []

        for forum in Forum.objects.all():
            effective_prefs[forum.pk] = forum.include_in_lastest_threads 
            if forum.is_trash: trash_forums.append(forum.pk)

        if poster:
            poster_prefs = cls.get_poster_preferences(poster)
            for fpk, include in list(poster_prefs.items()):
                effective_prefs[fpk] = include

        for fpk in trash_forums:
            effective_prefs[fpk] = False

        return effective_prefs

    def __str__(self):
        return '%s to %s' % (self.poster, self.forum)

class RateLimitedAccess(models.Model):
    limit_key = models.CharField(max_length=1024)
    address = models.GenericIPAddressField()
    at = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()

    @classmethod
    def check_limit(cls, limit_key, access_limit, address, window):
        now = timezone.now()
        cls.objects.filter(expires__lt=now).delete()
        cls.objects.create(
            limit_key=limit_key,
            address=address,
            expires=now + window
        )

        access_count = cls.objects.filter(
            limit_key=limit_key,
            address=address,
            at__gte=now - window
        ).count()

        return access_count < access_limit

    @classmethod
    def rate_limit(cls, limit_key, access_limit, window):
        def decorator(view):
            def wrapped_view(self, request, *args, **kwargs):
                addr = request.META.get(
                    utils.get_config('client_ip_field'), None)
                is_valid = cls.check_limit(
                    limit_key,
                    access_limit,
                    addr,
                    window
                )

                if is_valid:
                    return view(self, request, *args, **kwargs)
                else:
                    raise PermissionDenied('Rate limit exceded.')

            return wrapped_view
        return decorator
