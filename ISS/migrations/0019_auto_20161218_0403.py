# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def set_author(apps, schema_editor):
    Thread = apps.get_model('ISS', 'Thread')

    for thread in Thread.objects.all().iterator():
        thread.author = (thread.post_set
            .order_by('created')
            .select_related('author')
            [0]
            .author)

        thread.save()

def unset_author(apps, schema_editor):
    Thread = apps.get_model('ISS', 'Thread')

    for thread in Thread.objects.all().iterator():
        thread.author = None
        thread.save()
 
class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0018_thread_author'),
    ]

    operations = [
        migrations.RunPython(set_author)
    ]
