from django.db import models
from django.contrib import auth
from django.utils import timezone

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

class Thread(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    forum = models.ForeignKey(Forum)
    title = models.TextField()
    log = models.TextField()

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
