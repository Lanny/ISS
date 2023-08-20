# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0004_auto_20161022_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='normalized_username',
            field=models.CharField(default='FOOBAR', max_length=256),
            preserve_default=False,
        ),
    ]
