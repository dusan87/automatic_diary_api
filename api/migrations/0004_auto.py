# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('api', '0003_auto')]

    operations = [
        migrations.AlterField(
            field = models.ImageField(upload_to='users_photo'),
            name = 'image',
            model_name = 'androiduser',
        ),
    ]
