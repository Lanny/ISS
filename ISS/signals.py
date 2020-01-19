from django.core.cache import cache
from django.db import models
from django.db.models import signals
from django.dispatch import receiver

from ISS.models import *

@receiver(signals.post_save, sender=Post)
def update_thread_last_update_on_insert(sender, instance, created, **kwargs):
    if not created:
        # Edits don't bump threads.
        return

    thread = instance.thread

    if thread.last_update < instance.created:
        thread.last_update = instance.created
        thread.save()

@receiver(signals.post_delete, sender=Post)
def update_thread_last_update_on_delete(sender, instance, **kwargs):
    thread = instance.thread
    posts = thread.get_posts_in_thread_order(reverse=True)

    if posts.count() > 0:
        instance = posts[0]
        thread.last_update = instance.created
        thread.save()

@receiver(signals.post_save, sender=Thread)
def update_forum_last_update(sender, instance, created, **kwargs):
    thread = instance
    forum = thread.forum

    if forum.last_update < thread.last_update:
        forum.last_update = thread.last_update
        forum.save()

@receiver(signals.pre_save, sender=Poster)
def set_normalized_username(sender, instance, **kwargs):
    if not instance.normalized_username:
        instance.normalized_username = Poster.iss_normalize_username(instance.username)

@receiver(signals.pre_save, sender=Poster)
def set_normalized_email(sender, instance, **kwargs):
    if instance.email:
        instance.normalized_email = email_normalize.normalize(instance.email)

@receiver(signals.pre_save, sender=Thanks)
def reject_auto_erotic_athanksication(sender, instance, **kwargs):
    if instance.thanker.pk == instance.thankee.pk:
        raise IntegrityError('A user may not thank themselves')

@receiver(models.signals.pre_save, sender=FilterWord)
def invalidate_filter_cache(sender, instance, **kwargs):
    cache.delete('active_filters')

@receiver(models.signals.post_save, sender=Ban)
def invalidate_user_title_cache(sender, instance, *args, **kwargs):
    instance.subject.invalidate_user_title_cache()

def bust_acl_cache(sender, instance, **kwargs):
    cache.delete(AccessControlList._get_cache_key(instance.name))

signals.post_save.connect(bust_acl_cache, sender=AccessControlList)
signals.m2m_changed.connect(bust_acl_cache, AccessControlList.white_posters.through)
signals.m2m_changed.connect(bust_acl_cache, AccessControlList.black_posters.through)
signals.m2m_changed.connect(bust_acl_cache, AccessControlList.white_groups.through)
signals.m2m_changed.connect(bust_acl_cache, AccessControlList.black_groups.through)

def _bust_acl_for_posters(acl, posters):
    keys = [acl._get_poster_cross_cache_key(poster) for poster in posters]
    cache.delete_many(keys)

def bust_acl_user_list_cache(sender, model, instance, **kwargs):
    """
    The white or black list for a given ACL has changed, bust all the
    ACL x Poster cache entries for all the posters who entered or left one of
    the groups.
    """
    posters = model.objects.filter(pk__in=kwargs['pk_set'])
    _bust_acl_for_posters(instance, posters)

signals.m2m_changed.connect(bust_acl_user_list_cache, AccessControlList.white_posters.through)
signals.m2m_changed.connect(bust_acl_user_list_cache, AccessControlList.black_posters.through)

def bust_acl_group_membership_cache(sender, model, instance, **kwargs):
    """
    Posters have entered or left an ACG. For each ACL tied to the ACG, bust
    the ACL x Poster cache entries for the Posters who changed membership in
    the ACG.
    """
    posters = model.objects.filter(pk__in=kwargs['pk_set'])
    acg = instance

    for acl in acg.blacklisted_acls.all() | acg.whitelisted_acls.all():
        _bust_acl_for_posters(acl, posters)

signals.m2m_changed.connect(bust_acl_group_membership_cache, AccessControlGroup.members.through)

def bust_acl_group_list_cache(sender, model, instance, **kwargs):
    acgs = model.objects.filter(pk__in=kwargs['pk_set'])
    posters = Poster.objects.none()

    for acg in acgs:
        posters = posters | acg.members.all()

    _bust_acl_for_posters(instance, posters)

signals.m2m_changed.connect(bust_acl_group_list_cache, AccessControlList.white_groups.through)
signals.m2m_changed.connect(bust_acl_group_list_cache, AccessControlList.black_groups.through)
