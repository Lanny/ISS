# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0023_filterword'),
    ]

    operations = [
        migrations.AddField(
            model_name='filterword',
            name='case_sensitive',
            field=models.BooleanField(default=False),
        ),
    ]
