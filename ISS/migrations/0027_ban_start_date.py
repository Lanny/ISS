# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0026_ban'),
    ]

    operations = [
        migrations.AddField(
            model_name='ban',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 3, 11, 23, 33, 22, 176960, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
