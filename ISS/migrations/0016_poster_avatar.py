# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0015_auto_20161129_2051'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='avatar',
            field=models.ImageField(null=True, upload_to=b'avatars'),
        ),
    ]
