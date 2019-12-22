# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0020_auto_20161218_0409'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='auto_subscribe',
            field=models.IntegerField(default=1, choices=[(0, b'Never'), (1, b'On Post'), (2, b'On View')]),
        ),
    ]
