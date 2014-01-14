# encoding: utf8
from django.db import models, migrations
import django.utils.timezone
import datetime


class Migration(migrations.Migration):
    
    dependencies = []

    operations = [
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('password', models.CharField(max_length=128, verbose_name=u'password'),), ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name=u'last login'),), ('username', models.EmailField(unique=True, max_length=50, db_index=True),), ('first_name', models.CharField(max_length=50),), ('last_name', models.CharField(max_length=50),), ('country', models.CharField(default='', max_length=50, blank=True),), ('city', models.CharField(default='', max_length=50, blank=True),), ('image', models.ImageField(upload_to='users_photo', blank=True),), ('gender', models.CharField(default='M', max_length=2, blank=True, choices=(('M', 'Male',), ('F', 'Female',),)),), ('birth_day', models.DateField(default=datetime.date(2013, 2, 1), blank=True),), ('follows', models.ManyToManyField(to=u'api.AndroidUser'),)],
            bases = (models.Model,),
            options = {u'abstract': False},
            name = 'AndroidUser',
        ),
    ]
