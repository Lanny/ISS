# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-07-05 08:38


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0044_auto_20180705_0816'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='latestthreadsforumpreference',
            unique_together=set([('poster', 'forum')]),
        ),
    ]