# encoding: utf8
from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):
    
    dependencies = []

    operations = [
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('password', models.CharField(max_length=128, verbose_name=u'password'),), ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name=u'last login'),), ('first_name', models.CharField(max_length=50),), ('last_name', models.CharField(max_length=50),), ('username', models.EmailField(unique=True, max_length=50, db_index=True),), ('age', models.IntegerField(max_length=2),), ('image', models.ImageField(upload_to='users_photo', blank=True),)],
            bases = (models.Model,),
            options = {u'abstract': False},
            name = 'AndroidUser',
        ),
    ]
