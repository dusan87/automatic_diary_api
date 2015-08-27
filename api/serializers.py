from __future__ import absolute_import

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import AndroidUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AndroidUser
        fields = ('id', 'username', 'first_name',
                  'last_name', 'country', 'city',
                  'image', 'gender', 'birth_day',)