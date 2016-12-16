# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0016_poster_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='forum',
            name='is_trash',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='forum',
            name='priority',
            field=models.IntegerField(default=0),
        ),
    ]
