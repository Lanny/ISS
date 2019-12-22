# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0027_ban_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='ban',
            name='given_by',
            field=models.ForeignKey(related_name='bans_given', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL),
        ),
        migrations.AlterField(
            model_name='ban',
            name='subject',
            field=models.ForeignKey(related_name='bans', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
