__author__ = 'dusanristic'
from django import forms
from django.forms import fields
from django.contrib.auth.admin import UserCreationForm
from models import AndroidUser, UserLocation


class UserCreateForm(UserCreationForm):

    def clean_username(self):
        username = self.cleaned_data['username']

        try:
            # this is most weird thing that I needed to do
            self._meta.model._default_manager.get(username=username)
        except self._meta.model.DoesNotExist:
            return username

    class Meta:
        model = AndroidUser
        fields = ['first_name', 'last_name', 'username', 'country', 'birth_day', 'city', 'image', 'gender']


class LocationCreateForm(forms.Form):

    class Meta:
        fields = ['lat','long']

    def save(self):
        data = self.cleaned_data
        location = UserLocation(lat=data['lat'],long=data['long'])
        location.save()