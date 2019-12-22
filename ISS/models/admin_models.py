import re
import uuid
import pytz
from datetime import timedelta

from django.core.cache import cache
from django.urls import reverse
from django.db import models
from django.utils import timezone

class StaticPage(models.Model):
    page_id = models.CharField(max_length=1024, unique=True)
    page_title = models.CharField(max_length=1024)
    content = models.TextField()

    def __str__(self):
        return 'StaticPage: %s' % self.page_id

class FilterWord(models.Model):
    pattern = models.CharField(max_length=1024)
    replacement = models.CharField(max_length=1024)
    active = models.BooleanField(default=True)
    case_sensitive = models.BooleanField(default=False)
    _pattern_cache = None

    def _get_pat(self):
        if not self._pattern_cache:
            if self.case_sensitive:
                self._pattern_cache = re.compile(self.pattern)
            else:
                self._pattern_cache = re.compile(self.pattern, re.IGNORECASE)

        return self._pattern_cache

    def replace(self, text):
        return self._get_pat().sub(self.replacement, text)

    @classmethod
    def do_all_replacements(cls, text):
        filters = cache.get('active_filters')
        if filters == None:
            filters = list(cls.objects.filter(active=True))
            cache.set('active_filters', filters)

        for f in filters:
            text = f.replace(text)

        return text

class Ban(models.Model):
    subject = models.ForeignKey(
            'Poster',
            related_name="bans",
            on_delete=models.CASCADE)
    given_by = models.ForeignKey(
            'Poster',
            null=True,
            related_name="bans_given",
            on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    reason = models.CharField(max_length=1024)

    def is_active(self, now=None):
        if not now:
            now = timezone.now()

        return self.end_date == None or self.end_date > now

    def get_duration(self):
        if not self.end_date:
            return None

        return self.end_date - self.start_date

    def get_remaining_duration(self):
        if not self.end_date:
            return None

        return max(self.end_date - timezone.now(), timedelta(seconds=0))

    def __str__(self):
        return 'Ban on %s for reason: %s' % (
            self.subject.username, self.reason)

class IPBan(models.Model):
    on = models.GenericIPAddressField(null=True)
    expires = models.DateTimeField(default=None, null=True, blank=True)
    given = models.DateTimeField(auto_now_add=True)
    memo = models.TextField(blank=True, default='')

