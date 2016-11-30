# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0014_auto_20161128_0420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poster',
            name='allow_js',
            field=models.BooleanField(default=True),
        ),
    ]
