import random

from django.db import models
from django.core.exceptions import PermissionDenied
from django.utils import timezone

def default_code():
    return ''.join([chr(random.randint(65, 90) + random.randint(0,1) * 32)
                    for _ in range(256)])

class RegistrationCode(models.Model):
    code = models.CharField(max_length=256, default=default_code)
    expires = models.DateTimeField(null=True, default=None)

    generated_on = models.DateTimeField(default=timezone.now)
    generated_by = models.ForeignKey('ISS.Poster',
                                     related_name='reg_codes_generated',
                                     null=False)

    used_on = models.DateTimeField(null=True, default=None)
    used_by = models.OneToOneField('ISS.Poster',
                                   on_delete=models.CASCADE,
                                   null=True)

    def __unicode__(self):
        return '%s Registration Code' % (
            'Used' if self.used_by != None else 'Unused')
