# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0021_poster_auto_subscribe'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='posts_per_page',
            field=models.PositiveSmallIntegerField(default=20),
        ),
    ]
