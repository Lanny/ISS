# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ISS', '0013_auto_20161119_2100'),
    ]

    _forwards_sql = """
        CREATE INDEX post_contents_ft_index ON "ISS_post"
        USING GIN(to_tsvector('english', content));
    """
    _backwards_sql = 'DROP INDEX post_contents_ft_index;'

    operations = [
        migrations.RunSQL(_forwards_sql, _backwards_sql)
    ]
