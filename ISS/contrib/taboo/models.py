from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from ISS import models as iss_models
from ISS import utils as iss_utils 

class TabooProfile(models.Model):
    poster = models.OneToOneField(iss_models.Poster)
    mark = models.ForeignKey(iss_models.Poster, related_name='marked_by')
    phrase = models.CharField(max_length=1024)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)

    def matches_post(self, post):
        if post.author != self.mark:
            return False

        if not self.active:
            return False

        # Remove quoted blocks because they don't count.
        content = iss_utils.get_closure_bbc_parser().format(post.content)
        return self.phrase.lower() in content.lower()
