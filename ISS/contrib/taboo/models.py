from __future__ import unicode_literals
import random
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from django.dispatch import receiver
from django.template.loader import render_to_string

from ISS import models as iss_models
from ISS import utils as iss_utils 
from apps import TabooConfig

EXT = TabooConfig.name

MARKABLE_PROFILES_QUERY = """
SELECT
    profile.id,
    profile.poster_id,
    MAX(post.created)
FROM "taboo_tabooprofile" AS profile
JOIN "ISS_poster" AS poster
    ON profile.poster_id=poster.id
JOIN "ISS_post" as post
    ON post.author_id=poster.id
WHERE
    profile.active IS TRUE AND
    profile.poster_id != %s
GROUP BY profile.id
HAVING MAX(post.created) > (NOW() - INTERVAL %s);
"""

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

    def _get_candidate_marks(self):
        candidates = TabooProfile.objects.raw(
            MARKABLE_PROFILES_QUERY,
            [
                self.poster.pk,
                iss_utils.get_ext_config(EXT, 'time_to_inactivity')
            ])

        # De-serialize the profiles as the DB has already done most the heavy
        # lifting and we need to call `len()` on them.
        candidates = [c for c in candidates]

        return candidates

    def choose_mark_and_phrase(self):
        self.phrase = random.choice(
                iss_utils.get_ext_config(EXT, 'phrases'))
        candidates = self._get_candidate_marks()
        ccount = len(candidates)

        if ccount < 1:
            self.mark = None
        else:
            self.mark = candidates[random.randint(0, ccount-1)].poster

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

        TabooViolationRecord.objects.create( phrase=self.phrase,
            poster=self.poster,
            mark=self.mark,
            violating_post=post,
            victor_former_title=self.poster.custom_user_title,
            loser_former_title=self.mark.custom_user_title)

        self.mark.custom_user_title = iss_utils.get_ext_config(
            EXT,
            'usertitle_punishment')
        self.mark.save()

        self.poster.custom_user_title = iss_utils.get_ext_config(
            EXT,
            'usertitle_reward')
        self.poster.save()

        self.mark = None
        self.save()

        post.content += post_msg
        post.save()

    def get_successes(self):
        return TabooViolationRecord.objects.filter(poster=self.poster)

    def __unicode__(self):
        return self.poster.username

class TabooViolationRecord(models.Model):
    created = models.DateTimeField(default=timezone.now)
    phrase = models.CharField(max_length=1024)

    poster = models.ForeignKey(iss_models.Poster, related_name='taboo_successes')
    mark = models.ForeignKey(iss_models.Poster, related_name='taboo_failures')
    violating_post = models.ForeignKey(iss_models.Post, null=True,
                                       on_delete=models.SET_NULL)

    titles_rectified = models.BooleanField(default=False)
    victor_former_title = models.CharField(
            max_length=256,
            default=None,
            null=True)
    loser_former_title = models.CharField(
            max_length=256,
            default=None,
            null=True)

    @transaction.atomic
    def rectify_usertitles(self):
        title_period = iss_utils.get_ext_config(EXT, 'usertitle_duration')
        is_due = self.created < (timezone.now() - title_period)

        if is_due and not self.titles_rectified:
            self.poster.custom_user_title = self.victor_former_title
            self.poster.save()

            self.mark.custom_user_title = self.loser_former_title
            self.mark.save()

            self.titles_rectified = True
            self.save()

    #@transaction.atomic
    @classmethod
    def rectify_all_usertitles(cls):
        violations = cls.objects.filter(titles_rectified=False)
        for violation in violations:
            violation.rectify_usertitles()

@receiver(models.signals.post_save, sender=iss_models.Post)
def check_taboo_violation(sender, instance, created, **kwargs):
    if not created:
        return

    assassins = TabooProfile.objects.filter(mark=instance.author, active=True)

    for assassin in assassins:
        if assassin.matches_post(instance):
            assassin.execute_taboo(instance)
            return

@receiver(models.signals.post_save, sender=TabooProfile)
def taboo_profiles_changed(sender, instance, created, **kwargs):
    # Something changed, let's try finding a mark for every player
    needs_mark = TabooProfile.objects.all().filter(mark=None)

    for prof in needs_mark:
        # Recheck because this process changes the contents of the QS
        prof = TabooProfile.objects.get(pk=prof.pk)

        if prof.mark:
            # Looks like the profile has gotten a mark since we started
            return

        prof.choose_mark_and_phrase()

        if prof.mark:
            # Update instead of save as to avoid doing this recursively
            (TabooProfile.objects
                .filter(pk=prof.pk)
                .update(mark=prof.mark, phrase=prof.phrase))

            # Send out PM
            content = render_to_string(
                'taboo/bbc/new_mark.bbc',
                { 'mark': prof.mark, 'phrase': prof.phrase })

            iss_models.PrivateMessage.send_pm(
                iss_models.Poster.get_or_create_system_user(),
                [prof.poster],
                'Taboo: You\'ve received a new mark.',
                content)
