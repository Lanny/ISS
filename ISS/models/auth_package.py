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
        return u'%s(%d)' % (self.logic_package, self.pk)




