from __future__ import unicode_literals
import random

from django.db import models, transaction
from django.utils import timezone
from django.dispatch import receiver

from ISS import models as iss_models
from ISS import utils as iss_utils 
from apps import TabooConfig

EXT = TabooConfig.name

class TabooProfile(models.Model):
    poster = models.OneToOneField(iss_models.Poster, related_name='taboo_profile')
    mark = models.ForeignKey(iss_models.Poster, null=True,
                             related_name='marked_by')
    phrase = models.CharField(max_length=1024)
    active = models.BooleanField(default=True)
    last_registration = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)

    def matches_post(self, post):
        if post.author != self.mark:
            return False

        if not self.active:
            return False

        # Remove quoted blocks because they don't count.
        content = iss_utils.get_closure_bbc_parser().format(post.content)
        return self.phrase.lower() in content.lower()

    def choose_mark_and_phrase(self):
        self.phrase = 'foobar'
        candidates = (TabooProfile.objects.all()
            .filter(mark_id__not=self.pk))
        ccount = candidates.count()

        if ccount < 1:
            self.mark = None
        else:
            self.mark = candidates[random.randint(0, ccount-1)]

    @transaction.atomic
    def execute_taboo(self, post):
        violated_phrase = self.phrase
        ctx = {'phrase': violated_phrase}
        duration = iss_utils.get_ext_config(EXT, 'violation_duration')
        ban_reason = iss_utils.get_ext_config(EXT, 'ban_reason_tmpl') % ctx
        post_msg = iss_utils.get_ext_config(EXT, 'post_msg_tmpl') % ctx

        iss_models.Ban.objects.create(
            subject=post.author,
            given_by=iss_models.Poster.get_or_create_system_user(),
            end_date=timezone.now() + duration,
            reason=ban_reason)

        self.choose_mark_and_phrase()
        self.save()

        post.content += post_msg
        post.save()

@receiver(models.signals.post_save, sender=iss_models.Post)
def check_taboo_violation(sender, instance, created, **kwargs):
    if not created:
        return

    assassins = TabooProfile.objects.filter(mark=instance.author)

    for assassin in assassins:
        if assassin.matches_post(instance):
            assassin.execute_taboo(instance)
            return
