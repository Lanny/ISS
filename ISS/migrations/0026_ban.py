# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0025_poster_has_report_privilege'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ban',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('end_date', models.DateTimeField()),
                ('reason', models.CharField(max_length=1024)),
                ('subject', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
