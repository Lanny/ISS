# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-07-05 08:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0043_auto_20180408_2104'),
    ]

    operations = [
        migrations.CreateModel(
            name='LatestThreadsForumPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('include', models.BooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='forum',
            name='include_in_lastest_threads',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='latestthreadsforumpreference',
            name='forum',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ISS.Forum'),
        ),
        migrations.AddField(
            model_name='latestthreadsforumpreference',
            name='poster',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]