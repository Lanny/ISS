import json

from django.db import models
from django.core.exceptions import PermissionDenied

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

LOGIC_PACKAGES = (
    AdminRequiredLogicPackage,
    PermissiveLogicPackage
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

class AccessControlList(models.Model):
    base_acls = (
        ('CREATE_INVITE', False, ('INVITORS',), ()),
    )

    name = models.TextField(unique=True, blank=False, null=False)
    allow_by_default = models.BooleanField(default=False, null=False)

    white_posters = models.ManyToManyField('ISS.Poster',
                                           related_name='whitelisted_acls')
    black_posters = models.ManyToManyField('ISS.Poster',
                                           related_name='blacklisted_acls')
    white_groups = models.ManyToManyField('ISS.AccessControlGroup',
                                          related_name='whitelisted_acls')
    black_groups = models.ManyToManyField('ISS.AccessControlGroup',
                                          related_name='blacklisted_acls')

    def is_poster_authorized(self, poster):
        if self.black_posters.filter(pk=poster.pk).count():
            return False
        if self.white_posters.filter(pk=poster.pk).count():
            return True

        if self.black_groups.filter(members__pk=poster.pk).count():
            return False
        if self.white_groups.filter(members__pk=poster.pk).count():
            return True

        return self.allow_by_default

    @classmethod
    def get_acl(cls, name):
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

        return acl

