from django.db import models
from django.contrib import auth
from django.utils import timezone
from django.core.urlresolvers import reverse

class Poster(auth.models.AbstractBaseUser, auth.models.PermissionsMixin):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [ 'email' ]

    username = models.CharField(max_length=256, unique=True)
    email = models.EmailField()
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = auth.models.UserManager()

    def get_long_name(self):
        return self.username

    def get_short_name(self):
        return self.get_long_name()

class Forum(models.Model):
    name = models.TextField()
    description = models.TextField()

    def get_thread_count(self):
        return self.thread_set.count()

    def get_post_count(self):
        return Post.objects.filter(thread__forum_id=self.pk).count()

    def __unicode__(self):
        return self.name

class Thread(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    forum = models.ForeignKey(Forum)
    title = models.TextField()
    log = models.TextField(blank=True)

    def get_last_post(self):
        return (self.post_set
                    .order_by('created')
                    .select_related('author'))[0]

    def get_first_post(self):
        return (self.post_set
                    .order_by('-created')
                    .select_related('author'))[0]

    def get_author(self):
        return self.get_first_post().author

    def get_post_count(self):
        return self.post_set.count()

    def get_url(self, post=None):
        self_url = reverse('thread', kwargs={'thread_id': self.pk})

        return self_url

    def __unicode__(self):
        return self.title

class Post(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    thread = models.ForeignKey(Thread)
    content = models.TextField()
    author = models.ForeignKey(Poster)

class Thanks(models.Model):
    given = models.DateTimeField(auto_now_add=True)

    thanker = models.ForeignKey(Poster, related_name='thanks_given')
    thankee = models.ForeignKey(Poster, related_name='thanks_received')
    post = models.ForeignKey(Post)
