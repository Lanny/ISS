# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='forum',
            name='priority',
            field=models.IntegerField(default=2147483647),
        ),
    ]
