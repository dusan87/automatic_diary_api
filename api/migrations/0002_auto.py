# encoding: utf8
from django.db import models, migrations
import datetime


class Migration(migrations.Migration):
    
    dependencies = [('api', '0001_initial')]

    operations = [
        migrations.AddField(
            field = models.CharField(default='', max_length=50),
            name = 'city',
            model_name = 'androiduser',
        ),
        migrations.AddField(
            field = models.CharField(default='M', max_length=2, choices=(('M', 'Male',), ('F', 'Female',),)),
            name = 'gender',
            model_name = 'androiduser',
        ),
        migrations.AddField(
            field = models.DateField(default=datetime.date(2013, 2, 1)),
            name = 'birth_day',
            model_name = 'androiduser',
        ),
        migrations.AddField(
            field = models.CharField(default='', max_length=50),
            name = 'country',
            model_name = 'androiduser',
        ),
        migrations.RemoveField(
            name = 'age',
            model_name = 'androiduser',
        ),
    ]
