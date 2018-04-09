import re
import uuid
import pytz

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

class StaticPage(models.Model):
    page_id = models.CharField(max_length=1024, unique=True)
    page_title = models.CharField(max_length=1024)
    content = models.TextField()

    def __unicode__(self):
        return u'StaticPage: %s' % self.page_id

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
        if not filters:
            filters = cls.objects.filter(active=True)
            cache.set('active_filters', filters)

        for f in filters:
            text = f.replace(text)

        return text

class Ban(models.Model):
    subject = models.ForeignKey('Poster', related_name="bans")
    given_by = models.ForeignKey('Poster', null=True, related_name="bans_given")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    reason = models.CharField(max_length=1024)

    def is_active(self, now=None):
        if not now:
            now = timezone.now()

        return self.end_date == None or self.end_date > now

    def __unicode__(self):
        return u'Ban on %s for reason: %s' % (
            self.subject.username, self.reason)

class IPBan(models.Model):
    on = models.GenericIPAddressField(null=True)
    given = models.DateTimeField(auto_now_add=True)
    memo = models.TextField(blank=True, default='')

@receiver(models.signals.pre_save, sender=FilterWord)
def invalidate_filter_cache(sender, instance, **kwargs):
    cache.delete('active_filters')

@receiver(models.signals.post_save, sender=Ban)
def invalidate_user_title_cache(sender, instance, *args, **kwargs):
    instance.subject.invalidate_user_title_cache()
