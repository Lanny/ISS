import json

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.db import models

from ISS import utils

class BaseLogicPackage(object):
    def __init__(self, config=None):
        pass

    @classmethod
    def get_name(cls):
        raise NotImplemented()

    def is_authorized(self, auth_package, request):
        return False

class AdminRequiredLogicPackage(BaseLogicPackage):
    @classmethod
    def get_name(cls):
        return 'ADMIN_REQUIRED'

    def is_authorized(self, auth_package, request):
        return request.user.is_authenticated and request.user.is_staff

class PermissiveLogicPackage(BaseLogicPackage):
    @classmethod
    def get_name(cls):
        return 'PERMISSIVE'

    def is_authorized(self, auth_package, request):
        return True

class ACLLogicPackage(BaseLogicPackage):
    @classmethod
    def get_name(cls):
        return 'ACL_CONTROLLED'

    def is_authorized(self, auth_package, request):
        config = self.get_logic_config()
        ACL = AccessControlGroup.get_acl(config['ACL_NAME'])

        return ACL.is_poster_authorized(request.user)

LOGIC_PACKAGES = (
    AdminRequiredLogicPackage,
    PermissiveLogicPackage,
    ACLLogicPackage
)

PACKAGE_MAP = dict([(p.get_name(), p) for p in LOGIC_PACKAGES])

class AuthPackage(models.Model):
    logic_package = models.CharField(
        max_length=256,
        null=False,
        default='PERMISSIVE',
        choices=[(name, name) for name in PACKAGE_MAP.keys()])

    logic_config = models.TextField(blank=True)

    def get_logic_package(self):
        config = None

        if self.logic_config:
            config = json.loads(self.logic_config)

        package = PACKAGE_MAP[self.logic_package](config)

        return package

    def check_request(self, request):
        package = self.get_logic_package()
        return package.is_authorized(self, request)

    def validate_request(self, request):
        if not self.check_request(request):
            raise PermissionDenied('Not authorized.')

    def __unicode__(self):
        return u'%s (%d)' % (self.logic_package, self.pk)

class AccessControlGroup(models.Model):
    base_groups = (
        ('INVITORS',),
        ('SUPERUSERS',),
        ('MODS',),
        ('ADMINS',)
    )

    name = models.TextField(unique=True, blank=False, null=False)
    members = models.ManyToManyField('ISS.Poster')

    @classmethod
    def get_acg(cls, name):
        zero_or_one_qs = list(cls.objects.filter(name=name))
        acg = None

        if not zero_or_one_qs:
            acg_descs = filter(lambda desc: desc[0] == name, cls.base_groups)
            if acg_descs:
                (name,) = acg_descs[0]
                acg = cls(name=name)
                acg.save()
            else:
                raise Exception('No ACG with name "%s" exists.' % name)

        else:
            acg = zero_or_one_qs[0]

        return acg

    @classmethod
    def is_superuser(cls, poster):
        return bool(cls.get_acg('SUPERUSERS')
            .members
            .filter(pk=poster.pk)
            .count())

    def __unicode__(self):
        return self.name

class AccessControlList(models.Model):
    base_acls = (
        ('CREATE_INVITE', False, ('INVITORS', 'ADMINS'), ()),
        ('VIEW_INVITE_TREE', False, ('INVITORS', 'ADMINS'), ()),
        ('VIEW_IPS', False, ('SUPERUSERS', 'MODS'), ()),
        ('EDIT_ALL_POSTS', False, ('ADMINS',), ())
    )

    name = models.TextField(unique=True, blank=False, null=False)
    allow_by_default = models.BooleanField(default=False, null=False)

    white_posters = models.ManyToManyField('ISS.Poster',
                                           blank=True,
                                           related_name='whitelisted_acls')
    black_posters = models.ManyToManyField('ISS.Poster',
                                           blank=True,
                                           related_name='blacklisted_acls')
    white_groups = models.ManyToManyField('ISS.AccessControlGroup',
                                          blank=True,
                                          related_name='whitelisted_acls')
    black_groups = models.ManyToManyField('ISS.AccessControlGroup',
                                          blank=True,
                                          related_name='blacklisted_acls')

    @classmethod
    def _get_cache_key(cls, name):
        return 'auth:acl:name:%s' % name

    def _get_poster_cross_cache_key(self, poster):
        return 'auth:acl:name:%s:x:poster:%s' % (self.name, poster.pk)

    def _uncached_is_poster_authorized(self, poster):
        if isinstance(poster, AnonymousUser):
            return self.allow_by_default

        if self.black_posters.filter(pk=poster.pk).count():
            return False
        if self.white_posters.filter(pk=poster.pk).count():
            return True

        if self.black_groups.filter(members__pk=poster.pk).count():
            return False
        if self.white_groups.filter(members__pk=poster.pk).count():
            return True

        # Superusers have every permission not explicitly denied to them
        if AccessControlGroup.is_superuser(poster):
            return True

        return self.allow_by_default

    def is_poster_authorized(self, poster):
        cache_key = self._get_poster_cross_cache_key(poster)
        getter = lambda: self._uncached_is_poster_authorized(poster)
        return cache.get_or_set(cache_key, getter, 60*60*24)

    @classmethod
    def get_acl(cls, name):
        cache_key = cls._get_cache_key(name)
        cached_value = cache.get(cache_key)

        if cached_value:
            return cached_value

        zero_or_one_qs = list(cls.objects.filter(name=name))
        acl = None

        if not zero_or_one_qs:
            acl_descs = filter(lambda desc: desc[0] == name, cls.base_acls)
            if acl_descs:
                # ACL doesn't exist in the DB but it is in the base_acls list,
                # so we'll create it.
                name, allow_by_default, white_groups, black_groups = acl_descs[0]
                acl = cls(name=name, allow_by_default=allow_by_default)
                acl.save()

                for group in white_groups:
                    acl.white_groups.add(AccessControlGroup.get_acg(group))

                for group in black_groups:
                    acl.white_groups.add(AccessControlGroup.get_acg(group))
            else:
                raise Exception('No ACL with name "%s" exists.' % name)

        else:
            acl = zero_or_one_qs[0]

        if not cached_value:
            cache.set(cache_key, acl, 60*60*24)

        return acl

    def __unicode__(self):
        return self.name

