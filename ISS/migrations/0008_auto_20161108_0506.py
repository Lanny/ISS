# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0007_poster_backend'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='thanks',
            unique_together=set([('thanker', 'post')]),
        ),
    ]
