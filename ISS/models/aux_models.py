from django.db import models
from django.utils import timezone

from ISS import utils
from core_models import Forum, Poster, Thread


class LatestThreadsForumPreference(models.Model):
    class Meta:
        unique_together = ('poster', 'forum')

    poster = models.ForeignKey(Poster, null=False)
    forum = models.ForeignKey(Forum, null=False)

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
            for fpk, include in poster_prefs.items():
                effective_prefs[fpk] = include

        for fpk in trash_forums:
            effective_prefs[fpk] = False

        return effective_prefs

    def __unicode__(self):
        return u'%s to %s' % (self.poster, self.forum)
