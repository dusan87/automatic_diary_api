# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='androiduser',
            name='follows',
            field=models.ManyToManyField(related_name='follow', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='androiduser',
            name='last_login',
            field=models.DateTimeField(null=True, verbose_name='last login', blank=True),
        ),
        migrations.AlterField(
            model_name='usersinteractions',
            name='first_user',
            field=models.ForeignKey(related_name='first_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='usersinteractions',
            name='second_user',
            field=models.ForeignKey(related_name='second_user', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
