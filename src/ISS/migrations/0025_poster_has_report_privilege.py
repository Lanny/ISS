# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0024_filterword_case_sensitive'),
    ]

    operations = [
        migrations.AddField(
            model_name='poster',
            name='has_report_privilege',
            field=models.BooleanField(default=True),
        ),
    ]
