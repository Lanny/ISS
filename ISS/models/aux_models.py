from django.db import models
from django.utils import timezone

from core_models import Forum, Poster


class LatestThreadsForumPreference(models.Model):
    class Meta:
        unique_together = ('poster', 'forum')

    poster = models.ForeignKey(Poster, null=False)
    forum = models.ForeignKey(Forum, null=False)

    include = models.BooleanField(null=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s to %s' % (self.poster, self.forum)
