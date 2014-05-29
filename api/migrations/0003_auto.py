# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('api', '0002_usersinteractions')]

    operations = [
        migrations.AlterField(
            field = models.DateTimeField(null=True, blank=True),
            name = 'start_time',
            model_name = 'usersinteractions',
        ),
        migrations.AlterField(
            field = models.DateTimeField(null=True, blank=True),
            name = 'end_time',
            model_name = 'usersinteractions',
        ),
    ]
