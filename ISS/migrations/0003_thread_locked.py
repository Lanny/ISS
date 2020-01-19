# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0002_forum_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='locked',
            field=models.BooleanField(default=False),
        ),
    ]
