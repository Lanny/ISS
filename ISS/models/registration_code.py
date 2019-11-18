import random

from django.db import models
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone

from ISS import utils

def default_code():
    return ''.join([chr(random.randint(65, 90) + random.randint(0,1) * 32)
                    for _ in range(32)])

def default_expires():
    return timezone.now() + utils.get_config('invite_expiration_time')

class RegistrationCode(models.Model):
    code = models.CharField(max_length=256, default=default_code)
    expires = models.DateTimeField(null=True, default=default_expires)

    generated_on = models.DateTimeField(default=timezone.now)
    generated_by = models.ForeignKey('ISS.Poster',
                                     related_name='reg_codes_generated',
                                     on_delete=models.CASCADE)

    used_on = models.DateTimeField(null=True, default=None)
    used_by = models.OneToOneField('ISS.Poster',
                                   on_delete=models.CASCADE,
                                   null=True)

    def get_reg_url(self):
        return reverse('register-with-code') + '?code=%s' % self.code

    def __unicode__(self):
        return '%s Registration Code' % (
            'Used' if self.used_by != None else 'Unused')
