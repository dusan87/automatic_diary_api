# encoding: utf8
from django.db import models, migrations
import datetime


class Migration(migrations.Migration):
    
    dependencies = [('api', '0002_auto')]

    operations = [
        migrations.AlterField(
            field = models.CharField(default='', max_length=50, blank=True),
            name = 'city',
            model_name = 'androiduser',
        ),
        migrations.AlterField(
            field = models.CharField(default='', max_length=50, blank=True),
            name = 'country',
            model_name = 'androiduser',
        ),
        migrations.AlterField(
            field = models.CharField(default='M', max_length=2, blank=True, choices=(('M', 'Male',), ('F', 'Female',),)),
            name = 'gender',
            model_name = 'androiduser',
        ),
        migrations.AlterField(
            field = models.DateField(default=datetime.date(2013, 2, 1), blank=True),
            name = 'birth_day',
            model_name = 'androiduser',
        ),
    ]
