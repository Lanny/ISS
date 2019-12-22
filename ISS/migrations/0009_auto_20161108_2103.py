# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0008_auto_20161108_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='allow_avatars',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='poster',
            name='allow_image_embed',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='poster',
            name='allow_js',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='poster',
            name='custom_user_title',
            field=models.CharField(default=None, max_length=256, null=True),
        ),
    ]
