import re
import uuid
import pytz

from django.contrib import auth
from django.core.cache import cache
from django.urls import reverse
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

import email_normalize

from ISS import utils
from ISS.utils import HomoglyphNormalizer
from .auth_package import AuthPackage, AccessControlList
from .admin_models import Ban

min_time = timezone.make_aware(timezone.datetime.min,
                               timezone.get_default_timezone())

THEME_CHOICES = tuple(
    [(k, v['name']) for k,v in list(utils.get_config('themes').items())]
)

@models.fields.Field.register_lookup
class TSVectorLookup(models.Lookup):
    lookup_name = 'tsmatch'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        sql = 'to_tsvector(\'english\', %s) @@ plainto_tsquery(\'english\', %s)' % (
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
    normalized_username = models.CharField(max_length=2048)
    email = models.EmailField()

    # TODO: Make this non-nullable somehow
    normalized_email = models.EmailField(null=True)

    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    has_report_privilege = models.BooleanField(default=True)
    tripphrase = models.CharField(max_length=256, null=True, blank=True)

    recovery_code = models.CharField(max_length=256, null=True, blank=True,
                                     default=None)
    recovery_expiration = models.DateTimeField(default=timezone.now)
    email_verification_code = models.UUIDField(
        default=uuid.uuid4,
        null=True,
        blank=True)
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
    allow_video_embed = models.BooleanField(default=True)
    enable_editor_buttons = models.BooleanField(default=False)
    allow_avatars = models.BooleanField(default=True)
    auto_subscribe = models.IntegerField(
        choices=SUBSCRIBE_CHOICES,
        default=1,
        blank=False,
        null=False)
    theme = models.CharField(
        max_length=256,
        null=False,
        default=utils.get_config('default_theme'),
        choices=THEME_CHOICES)
    pgp_key = models.TextField(default='', blank=True)

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

    def invalidate_user_title_cache(self):
        cache_key = self._user_title_cache_key % self.pk
        cache.delete(cache_key)

    def get_user_title(self):
        cache_key = self._user_title_cache_key % self.pk
        cached_value = cache.get(cache_key)

        if cached_value:
            return cached_value

        cache_duration = 60*30
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

            ban = self.get_longest_ban()
            if ban:
                remaining = ban.get_remaining_duration()

                if remaining:
                    cache_duration = int(remaining.total_seconds())
                else:
                    # User is perma-banned, cache long-term
                    cache_duration = 60*60*24*7
            else:
                cache_duration = 60*60*24*7

        cache.set(cache_key, title, cache_duration)
        return title

    def get_nojs(self):
        return self.allow_js

    def get_inbox_badge_count(self):
        return (self.pms_received
            .filter(inbox=self)
            .filter(read=False)
            .count())

    def get_pending_bans(self):
        subject_query = Q(subject=self)
        active_query = Q(end_date__gt=timezone.now()) | Q(end_date__isnull=True)
        return Ban.objects.filter(subject_query & active_query)

    def get_longest_ban(self):
       sorted_bans = self.get_pending_bans().order_by('-end_date')

       if len(sorted_bans):
           return sorted_bans[0]
       else:
           return None

    def is_banned(self):
        pending_bans = self.get_pending_bans()
        if pending_bans.count() > 0:
            return True

        return False

    def get_ban_reason(self):
        ban = self.get_longest_ban()
        return ban.reason if ban else 'Not Banned (you should never see this)'

    def can_report(self):
        return self.has_report_privilege

    def get_alts(self):
        ip_addrs = (Post.objects.filter(author=self)
            .distinct('posted_from')
            .values_list('posted_from', flat=True))

        evidence = (Post.objects.filter(posted_from__in=ip_addrs)
            .exclude(author=self)
            .distinct('author'))

        return [{'poster': p.author, 'addr': p.posted_from} for p in evidence]

    def can_auto_anonymize(self):
        min_age = utils.get_config('min_account_age_to_anonymize')
        min_posts = utils.get_config('min_posts_to_anonymize')

        account_age = (timezone.now() - self.date_joined)
        post_count = self.post_set.count()

        return  account_age >= min_age and post_count >= min_posts

    @transaction.atomic
    def merge_into(self, other):
        """
        Reassigns all the records that tie to this user to another one and
        disables this user afterwards.
        """
        
        Thread.objects.filter(author=self).update(author=other)
        Post.objects.filter(author=self).update(author=other)

        for thanks in self.thanks_given.all():
            try:
                with transaction.atomic():
                    thanks.thanker = other
                    thanks.save()
            except IntegrityError:
                thanks.delete()

        for thanks in self.thanks_received.all():
            try:
                with transaction.atomic():
                    thanks.thankee = other
                    thanks.save()
            except IntegrityError:
                thanks.delete()

        self.save()

    @classmethod
    def get_or_create_junk_user(cls):
        return cls._get_or_create_user(utils.get_config('junk_user_username'))

    @classmethod
    def get_or_create_system_user(cls):
        return cls._get_or_create_user(utils.get_config('system_user_username'))

    @classmethod
    def _get_or_create_user(cls, username):
        username = str(username)
        norm_username = cls.iss_normalize_username(username)

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
    def iss_normalize_username(cls, username):
        norm = HomoglyphNormalizer.normalize_homoglyphs(username)
        norm = re.sub('\s', '', norm)

        return norm

    @classmethod
    def normalize_username(cls, username):
        # We have our own username normalization, so we disable django's
        return username

    def embed_images(self):
        return self.allow_image_embed

    def embed_video(self):
        return self.allow_video_embed

class Category(models.Model):
    name = models.CharField(max_length=256)
    priority = models.IntegerField(default=0, null=False)

    def __str__(self):
        return self.name

def default_auth_pack():
    return AuthPackage.objects.create().pk

class Forum(models.Model):
    category = models.ForeignKey(
            Category,
            null=True,
            default=None,
            on_delete=models.CASCADE)
    name = models.TextField()
    description = models.TextField()
    priority = models.IntegerField(default=0, null=False)
    last_update = models.DateTimeField(default=timezone.now)
    is_trash = models.BooleanField(default=False)
    include_in_lastest_threads = models.BooleanField(default=True, null=False)

    create_thread_pack = models.ForeignKey(
        AuthPackage,
        related_name='thread_creation_pack',
        default=default_auth_pack,
        on_delete=models.CASCADE)

    create_post_pack = models.ForeignKey(
        AuthPackage,
        related_name='post_creation_pack',
        default=default_auth_pack,
        on_delete=models.CASCADE)

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
        if hasattr(self, 'thread_count'):
            return self.thread_count
        else:
            return self.thread_set.count()

    def get_post_count(self):
        if hasattr(self, 'post_count'):
            return self.post_count
        else:
            return Post.objects.filter(thread__forum_id=self.pk).count()

    def get_url(self):
        return reverse('thread-index', kwargs={'forum_id': self.pk})

    def __str__(self):
        return self.name

class Thread(models.Model):
    created = models.DateTimeField(default=timezone.now)
    last_update = models.DateTimeField(default=timezone.now, db_index=True)
    locked = models.BooleanField(default=False)
    stickied = models.BooleanField(default=False)

    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    author = models.ForeignKey(Poster, on_delete=models.CASCADE)
    title = models.TextField()
    log = models.TextField(blank=True)

    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self._flag_cache = {}

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
        if not hasattr(self, 'post_count'):
            self.post_count = self.post_set.count()

        return self.post_count

    def get_posts_in_thread_order(self, reverse=False):
        return self.post_set.order_by('-created' if reverse else 'created')

    def get_url(self, page=None):
        url = reverse('thread', kwargs={'thread_id': self.pk})
        if page and page > 1:
            url = '%s?p=%d' % (url, page)

        return url

    def get_jump_post(self, user):
        """
        Returns the last undread post for a user IF the user has a living
        flag against this thread. Otherwise none.
        """
        if not user.is_authenticated:
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
        if not (user.pk in self._flag_cache):
            flag, created = ThreadFlag.objects.get_or_create(
                poster=user,
                thread=self)

            if created and save:
                flag.save()

            self._flag_cache[user.pk] = flag

        return self._flag_cache[user.pk]

    def has_unread_posts(self, user):
        if not user.is_authenticated:
            return True

        flag = self._get_flag(user, False)

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

    def has_been_read(self, user):
        return bool(self._get_flag(user, save=False).last_read_date)

    def is_subscribed(self, user):
        return self._get_flag(user, save=False).subscribed

    def subscribe(self, user):
        flag = self._get_flag(user, save=False)
        flag.subscribed = True
        flag.save()

    def unsubscribe(self, user):
        flag = self._get_flag(user, save=False)
        flag.subscribed = False
        flag.save()

    def update_subscriptions_on_post_deletion(self, post):
        pass

    def __str__(self):
        return self.title

class Post(models.Model):
    created = models.DateTimeField(default=timezone.now)

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    author = models.ForeignKey(Poster, on_delete=models.CASCADE)
    content = models.TextField()
    has_been_edited = models.BooleanField(default=False)

    posted_from = models.GenericIPAddressField(null=True)

    def quote_content(self):
        parser = utils.get_closure_bbc_parser()
        body = parser.format(self.content)

        template = '[quote pk=%d author="%s"]\n%s\n[/quote]'
        return template % (self.pk, self.author.username, body)

    def get_url(self):
        return reverse('post', kwargs={'post_id': self.pk})

    def get_thanker_pks(self):
        return {t.thanker_id for t in self.thanks_set.all()}

    def can_be_edited_by(self, poster, is_banned=None):
        """
        Returns true if the poster can edit this post. Banned users can not
        edit posts. Figuring out if a user is banned requires querying the DB,
        it can become costly to do this over and over in contexts like post
        lists, so if the caller knows the poster's banned status then they can
        pass that and we'll skip this check.
        """
        if is_banned == None:
            is_banned = poster.is_banned()

        if is_banned:
            return False

        if poster == self.author:
            return True

        acl = AccessControlList.get_acl('EDIT_ALL_POSTS')
        return acl.is_poster_authorized(poster)
        

    def _rectify_subscriptions_on_removal_from_thread(self):
        """
        Somewhat complex. When a post is removed from a thread some ThreadFlags
        will have an FK to it on their last_read_post key. We need to set
        last_read_post to the prior post in thread order (or delete the sub if
        the last read was the op) and update thread last_updated field.
        """
        impacted_flags = ThreadFlag.objects.filter(last_read_post=self)
        thread = self.thread

        if impacted_flags.count():
            posts_in_thread = list(thread.get_posts_in_thread_order(reverse=True))

            for idx, post in enumerate(posts_in_thread):
                if post.pk == self.pk:
                    try:
                        prior = posts_in_thread[idx+1]
                        impacted_flags.update(last_read_post=prior)
                    except IndexError:
                        # Subscription pointed to the OP. Burn it.
                        impacted_flags.delete()

            # Find the last post in thread order and set thread.last_update to
            # its create date.
            last_post = None
            if posts_in_thread[0].pk != self.pk:
                last_post = posts_in_thread[0]
            elif len(posts_in_thread) > 1:
                last_post = posts_in_thread[1]
            else:
                # OP was only post in thread and just got removed. Uhh, should
                # probably delete but this situation should be naturally
                # possible. Let's raise an exception instead
                raise Exception('Unexpected post removal scenario.')

            thread.last_update = last_post.created
            thread.save()

    def move_to_thread(self, target_thread):
        self._rectify_subscriptions_on_removal_from_thread()
        self.thread = target_thread
        self.save()

    def delete(self, *args, **kwargs):
        self._rectify_subscriptions_on_removal_from_thread()
        super(Post, self).delete(*args, **kwargs)

    def show_edit_line(self):
        if not self.has_been_edited:
            return False

        snapshot = self.get_last_edit_snapshot()

        edit_time = snapshot.time - self.created
        max_seconds = utils.get_config('ninja_edit_grace_time')

        return edit_time.total_seconds() > max_seconds

    def get_last_edit_snapshot(self):
        return self.postsnapshot_set.all().order_by('-time')[0]

class PostSnapshot(models.Model):
    time = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField()

    # Who made the edit trigging the creation of this snapshot?
    obsolesced_by = models.ForeignKey(Poster, on_delete=models.CASCADE)
    obsolescing_ip = models.GenericIPAddressField(null=True)


class Thanks(models.Model):
    class Meta:
        unique_together = ('thanker', 'post')

    given = models.DateTimeField(auto_now_add=True)

    thanker = models.ForeignKey(
            Poster,
            related_name='thanks_given',
            on_delete=models.CASCADE)
    thankee = models.ForeignKey(
            Poster,
            related_name='thanks_received',
            on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

class ThreadFlag(models.Model):
    class Meta:
        unique_together = ('thread', 'poster')

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    poster = models.ForeignKey(Poster, on_delete=models.CASCADE)

    last_read_post = models.ForeignKey(Post,
                                       null=True,
                                       on_delete=models.SET_NULL)
    last_read_date = models.DateTimeField(null=True)
    subscribed = models.BooleanField(default=False)

class ForumFlag(models.Model):
    class Meta:
        unique_together = ('forum', 'poster')

    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    poster = models.ForeignKey(Poster, on_delete=models.CASCADE)

    last_read_date = models.DateTimeField(null=True)

class PrivateMessage(models.Model):
    chain = models.UUIDField(default=uuid.uuid4, editable=False)
    created = models.DateTimeField(default=timezone.now)

    sender = models.ForeignKey(
            Poster,
            related_name='pms_sent',
            on_delete=models.CASCADE)
    receiver = models.ForeignKey(
            Poster,
            related_name='pms_received',
            on_delete=models.CASCADE)
    inbox = models.ForeignKey(Poster, on_delete=models.CASCADE)

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

    def __str__(self):
        return self.subject

    @classmethod
    def send_pm(cls, sender, receivers, subject, content, chain=None):
        chain_id = chain if chain else uuid.uuid4()
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
