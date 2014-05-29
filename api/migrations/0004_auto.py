# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('api', '0003_auto')]

    operations = [
        migrations.AddField(
            field = models.DateTimeField(auto_now_add=True, null=True),
            name = 'last_update',
            model_name = 'userlocation',
        ),
        migrations.AlterField(
            field = models.DateTimeField(auto_now_add=True),
            name = 'start_time',
            model_name = 'usersinteractions',
        ),
    ]
