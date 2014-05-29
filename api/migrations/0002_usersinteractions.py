# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):
    
    dependencies = [('api', '0001_initial')]

    operations = [
        migrations.CreateModel(
            fields = [(u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True),), ('type', models.CharField(max_length=50),), ('first_user', models.ForeignKey(to=u'api.AndroidUser', to_field=u'id'),), ('second_user', models.ForeignKey(to=u'api.AndroidUser', to_field=u'id', null=True),), ('location', models.ForeignKey(to=u'api.UserLocation', to_field=u'id'),), ('start_time', models.DateTimeField(blank=True),), ('end_time', models.DateTimeField(blank=True),), ('phone_number', models.CharField(max_length=50, null=True, blank=True),)],
            bases = (models.Model,),
            options = {},
            name = 'UsersInteractions',
        ),
    ]
