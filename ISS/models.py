import re
import uuid
import pytz

from django.contrib import auth
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError, transaction
from django.dispatch import receiver
from django.utils import timezone

from ISS import utils

min_time = timezone.make_aware(timezone.datetime.min,
                               timezone.get_default_timezone())

@models.fields.Field.register_lookup
class TSVectorLookup(models.Lookup):
    lookup_name = 'tsmatch'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        sql = 'to_tsvector(\'english\', %s) @@ to_tsquery(\'english\', %s)' % (
            lhs, rhs)

        return sql, params
    

class Poster(auth.models.AbstractBaseUser, auth.models.PermissionsMixin):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [ 'email' ]
    SUBSCRIBE_CHOICES = (
        (0, 'Never'),
        (1, 'On Post'),
        (2, 'On View'),
    )

    _user_title_cache_key = 'posters:%d:usertitle'

    username = models.CharField(max_length=256, unique=True)
    normalized_username = models.CharField(max_length=256)
    email = models.EmailField()
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    has_report_privilege = models.BooleanField(default=True)

    avatar = models.ImageField(upload_to='avatars', null=True)

    posts_per_page = models.PositiveSmallIntegerField(default=20)
    custom_user_title = models.CharField(max_length=256, null=True,
                                         default=None, blank=True)
    timezone = models.CharField(
        max_length=256,
        null=False,
        default='UTC',
        choices=[(tz, tz) for tz in pytz.common_timezones])

    allow_js = models.BooleanField(default=True)
    allow_image_embed = models.BooleanField(default=True)
    allow_avatars = models.BooleanField(default=True)
    auto_subscribe = models.IntegerField(
        choices=SUBSCRIBE_CHOICES,
        default=1,
        blank=False,
        null=False)

    # For support of vB backends
    backend = models.TextField(
        default='django.contrib.auth.backends.ModelBackend')

    objects = auth.models.UserManager()

    def get_long_name(self):
        return self.username

    def get_short_name(self):
        return self.get_long_name()

    def get_url(self):
        return reverse('user-profile', kwargs={'user_id': self.pk})

    def get_post_count(self):
        return self.post_set.count()

    def show_email(self):
        return False

    def can_post(self):
        return self.is_active

    def clean(self):
        # Django decided to declare their own normalize_username and this calls
        # into that so we'll just skip this step all together.
        pass

    def invalidate_user_title_cache(self):
        cache_key = self._user_title_cache_key % self.pk
        cache.delete(cache_key)

    def get_user_title(self):
        cache_key = self._user_title_cache_key % self.pk
        cached_value = cache.get(cache_key)

        if cached_value:
            return cached_value

        if self.custom_user_title:
            title = self.custom_user_title
        else:
            post_count = self.get_post_count()
            title = None

            for threshold, rank_title in utils.get_config('title_ladder'):
                if post_count >= threshold:
                    title = rank_title
                    break

        if self.is_banned():
            title += ' (banned)'

        cache.set(cache_key, title, 60*30)
        return title

    def get_nojs(self):
        return self.allow_js

    def get_inbox_badge_count(self):
        return (self.pms_received
            .filter(inbox=self)
            .filter(read=False)
            .count())

    def get_pending_bans(self):
       return Ban.objects.filter(subject=self, end_date__gt=timezone.now())

    def is_banned(self):
        if not self.is_active:
            return True

        pending_bans = self.get_pending_bans()
        if pending_bans.count() > 0:
            return True

        return False

    def get_ban_reason(self):
        pending_bans = self.get_pending_bans().order_by('-end_date')

        return pending_bans[0].reason

    def can_report(self):
        return self.has_report_privilege

    @transaction.atomic
    def merge_into(self, other):
        """
        Reassigns all the records that tie to this user to another one and
        disables this user afterwards.
        """
        
        Thread.objects.filter(author=self).update(author=other)
        Post.objects.filter(author=self).update(author=other)
        Thanks.objects.filter(thanker=self).update(thanker=other)
        Thanks.objects.filter(thankee=self).update(thankee=other)

        self.save()

    @classmethod
    def get_or_create_junk_user(cls):
        return cls._get_or_create_user(utils.get_config('junk_user_username'))

    @classmethod
    def get_or_create_system_user(cls):
        return cls._get_or_create_user(utils.get_config('system_user_username'))

    @classmethod
    def _get_or_create_user(cls, username):
        norm_username = cls.normalize_username(username)

        try:
            user = cls.objects.get(normalized_username=norm_username)

            if user.is_active:
                user.is_active = False
                user.save()

        except cls.DoesNotExist:
            user = cls(
                username = username,
                email = 'not.a.email.address@nowhere.space',
                is_active = False)
            user.save()

        return user

    @classmethod
    def normalize_username(cls, username):
        norm = username.lower()
        norm = re.sub('\s', '', norm)

        return norm

    def embed_images(self):
        return self.allow_image_embed

class Forum(models.Model):
    name = models.TextField()
    description = models.TextField()
    priority = models.IntegerField(default=0, null=False)
    last_update = models.DateTimeField(default=timezone.now)
    is_trash = models.BooleanField(default=False)

    _flag_cache = None

    def _get_flag(self, user):
        if not self._flag_cache:
            self._flag_cache, created = ForumFlag.objects.get_or_create(
                poster=user,
                forum=self)

        return self._flag_cache

    def mark_read(self, user):
        flag = self._get_flag(user)
        flag.last_read_date = timezone.now()
        flag.save()

    def is_unread(self, user):
        flag = self._get_flag(user)

        if not flag.last_read_date or flag.last_read_date < self.last_update:
            return True
        else:
            return False

    def get_thread_count(self):
        return self.thread_set.count()

    def get_post_count(self):
        return Post.objects.filter(thread__forum_id=self.pk).count()

    def get_url(self):
        return reverse('thread-index', kwargs={'forum_id': self.pk})

    def __unicode__(self):
        return self.name

class Thread(models.Model):
    created = models.DateTimeField(default=timezone.now)
    last_update = models.DateTimeField(default=timezone.now)
    locked = models.BooleanField(default=False)

    forum = models.ForeignKey(Forum)
    author = models.ForeignKey(Poster)
    title = models.TextField()
    log = models.TextField(blank=True)

    _flag_cache = None

    def get_last_post(self):
        return (self.post_set
                    .order_by('-created')
                    .select_related('author'))[0]

    def get_first_post(self):
        return (self.post_set
                    .order_by('created')
                    .select_related('author'))[0]

    def get_author(self):
        return self.author

    def get_post_count(self):
        return self.post_set.count()

    def get_posts_in_thread_order(self, reverse=False):
        return self.post_set.order_by('-created' if reverse else 'created')

    def get_url(self):
        return reverse('thread', kwargs={'thread_id': self.pk})

    def get_jump_post(self, user):
        """
        Returns the last undread post for a user IF the user has a living
        flag against this thread. Otherwise none.
        """
        if not user.is_authenticated():
            return None

        preceeding_date = self._get_flag(user, False).last_read_date

        if not preceeding_date:
            return None

        post = (self.get_posts_in_thread_order()
            .filter(created__gt=preceeding_date)
            .first())

        return post

    def can_reply(self):
        return not self.locked

    def _get_flag(self, user, save=True):
        if not self._flag_cache:
            self._flag_cache, created = ThreadFlag.objects.get_or_create(
                poster=user,
                thread=self)

            if created and save:
                self._flag_cache.save()

        return self._flag_cache

    def has_unread_posts(self, user):
        if not user.is_authenticated():
            return True

        flag = self._get_flag(user)

        if not flag.last_read_date or flag.last_read_date < self.last_update:
            return True
        else:
            return False

    def mark_read(self, user, post=None):
        flag = self._get_flag(user, save=False)

        if post is None:
            post = self.get_last_post()

        if (not flag.last_read_post or
                flag.last_read_post.created < post.created):
            flag.last_read_post = post
            flag.last_read_date = post.created

        flag.save()

    def subscribe(self, user):
        flag = self._get_flag(user, save=False)
        flag.subscribed = True

        flag.save()

    def __unicode__(self):
        return self.title

class Post(models.Model):
    created = models.DateTimeField(default=timezone.now)

    thread = models.ForeignKey(Thread)
    content = models.TextField()
    author = models.ForeignKey(Poster)

    def quote_content(self):
        parser = utils.get_closure_bbc_parser()
        body = parser.format(self.content)

        template = '[quote pk=%d author=%s]\n%s\n[/quote]'
        return template % (self.pk, self.author.username, body)

    def get_url(self):
        return reverse('post', kwargs={'post_id': self.pk})

    def get_thanker_pks(self):
        return {t.thanker_id for t in self.thanks_set.all()}

class Thanks(models.Model):
    class Meta:
        unique_together = ('thanker', 'post')

    given = models.DateTimeField(auto_now_add=True)

    thanker = models.ForeignKey(Poster, related_name='thanks_given')
    thankee = models.ForeignKey(Poster, related_name='thanks_received')
    post = models.ForeignKey(Post)

class ThreadFlag(models.Model):
    class Meta:
        unique_together = ('thread', 'poster')

    thread = models.ForeignKey(Thread)
    poster = models.ForeignKey(Poster)

    last_read_post = models.ForeignKey(Post, null=True)
    last_read_date = models.DateTimeField(null=True)
    subscribed = models.BooleanField(default=False)

class ForumFlag(models.Model):
    class Meta:
        unique_together = ('forum', 'poster')

    forum = models.ForeignKey(Forum)
    poster = models.ForeignKey(Poster)

    last_read_date = models.DateTimeField(null=True)

class PrivateMessage(models.Model):
    chain = models.UUIDField(default=uuid.uuid4, editable=False)
    created = models.DateTimeField(default=timezone.now)

    sender = models.ForeignKey(Poster, related_name='pms_sent')
    receiver = models.ForeignKey(Poster, related_name='pms_received')
    inbox = models.ForeignKey(Poster)

    subject = models.CharField(max_length=256)
    content = models.TextField()
    read = models.BooleanField(default=False)

    def quote_content(self):
        parser = utils.get_closure_bbc_parser()
        body = parser.format(self.content)

        template = '[quote author=%s]\n%s\n[/quote]'
        return template % (self.sender.username, body)

    def mark_read(self, commit=True):
        self.read = True

        if commit:
            self.save()

    def __unicode__(self):
        return self.subject

    @classmethod
    def send_pm(cls, sender, receivers, subject, content, chain=None):
        chain_id = chain_id if chain else uuid.uuid4()
        sent_copies = []
        kept_copies = []

        for receiver in receivers:
            opts = {
                'sender': sender,
                'receiver': receiver,
                'inbox': receiver,
                'subject': subject,
                'content': content,
                'chain': chain_id
            }

            # Receiver's copy
            pm = PrivateMessage(**opts) 
            pm.save()
            sent_copies.append(pm)

            if sender != receiver:
                # Sender's copy
                opts['inbox'] = sender
                pm = PrivateMessage(**opts)
                pm.save()
                kept_copies.append(pm)

        return (sent_copies, kept_copies)

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
    subject = models.ForeignKey(Poster, related_name="bans")
    given_by = models.ForeignKey(Poster, null=True, related_name="bans_given")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    reason = models.CharField(max_length=1024)

    def is_active(self, now=None):
        if not now:
            now = timezone.now()

        print now,
        print self.end_date
        return self.end_date > now

@receiver(models.signals.post_save, sender=Post)
def update_thread_last_update_on_insert(sender, instance, created, **kwargs):
    if not created:
        # Edits don't bump threads.
        return

    thread = instance.thread

    if thread.last_update < instance.created:
        thread.last_update = instance.created
        thread.save()

@receiver(models.signals.post_delete, sender=Post)
def update_thread_last_update_on_delete(sender, instance, **kwargs):
    thread = instance.thread
    instance = thread.get_posts_in_thread_order(reverse=True)[0]
    thread.last_update = instance.created
    thread.save()

@receiver(models.signals.post_save, sender=Thread)
def update_forum_last_update(sender, instance, created, **kwargs):
    thread = instance
    forum = thread.forum

    if forum.last_update < thread.last_update:
        forum.last_update = thread.last_update
        forum.save()

@receiver(models.signals.pre_save, sender=Poster)
def set_normalized_username(sender, instance, **kwargs):
    instance.normalized_username = Poster.normalize_username(instance.username)

@receiver(models.signals.pre_save, sender=Thanks)
def reject_auto_erotic_athanksication(sender, instance, **kwargs):
    if instance.thanker.pk == instance.thankee.pk:
        raise IntegrityError('A user may not thank themselves')

@receiver(models.signals.pre_save, sender=FilterWord)
def invalidate_filter_cache(sender, instance, **kwargs):
    cache.delete('active_filters')

@receiver(models.signals.post_save, sender=Ban)
def invalidate_user_title_cache(sender, instance, *args, **kwargs):
    instance.subject.invalidate_user_title_cache()
