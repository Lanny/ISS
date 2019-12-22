# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0009_auto_20161108_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poster',
            name='custom_user_title',
            field=models.CharField(default=None, max_length=256, null=True, blank=True),
        ),
    ]
