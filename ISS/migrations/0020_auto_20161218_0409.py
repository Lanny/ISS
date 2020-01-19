# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0019_auto_20161218_0403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thread',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
