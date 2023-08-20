# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0011_poster_timezone'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('chain', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('subject', models.CharField(max_length=256)),
                ('content', models.TextField()),
                ('receiver', models.ForeignKey(related_name='pms_received', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('sender', models.ForeignKey(related_name='pms_sent', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
    ]
