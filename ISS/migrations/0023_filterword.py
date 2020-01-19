# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0022_poster_posts_per_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilterWord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pattern', models.CharField(max_length=1024)),
                ('replacement', models.CharField(max_length=1024)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
    ]
