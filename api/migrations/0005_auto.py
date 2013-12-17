# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('api', '0004_auto')]

    operations = [
        migrations.AlterField(
            field = models.ImageField(upload_to='users_photo', blank=True),
            name = 'image',
            model_name = 'androiduser',
        ),
    ]
