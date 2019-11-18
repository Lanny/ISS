# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0003_thread_locked'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThreadFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_read_date', models.DateTimeField(null=True)),
                ('subscribed', models.BooleanField(default=False)),
                ('last_read_post', models.ForeignKey(to='ISS.Post', null=True)),
                ('poster', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(to='ISS.Thread')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='threadflag',
            unique_together=set([('thread', 'poster')]),
        ),
    ]
