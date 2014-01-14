__author__ = 'dusanristic'
from django import forms
from django.forms import fields
from django.contrib.auth.admin import UserCreationForm
from models import AndroidUser


class UserCreateForm(UserCreationForm):
        class Meta:
            model = AndroidUser
            fields = ['first_name', 'last_name', 'username', 'country', 'birth_day', 'city', 'image', 'gender']

