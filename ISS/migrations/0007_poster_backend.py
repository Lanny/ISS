# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0006_auto_20161106_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='backend',
            field=models.TextField(default=b'django.contrib.auth.backends.ModelBackend'),
        ),
    ]
