__author__ = 'dusanristic'

# django
from django import forms
from django.contrib.auth.admin import UserCreationForm

# project
from models import User, UserLocation


class UserCreateForm(UserCreationForm):

    def clean_email(self):
        email = self.cleaned_data['email']

        try:
            # this is most weird thing that I needed to do
            self._meta.model._default_manager.get(email=email)
        except self._meta.model.DoesNotExist:
            return email

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'country', 'birth_day', 'city', 'image', 'gender']


class LocationCreateForm(forms.Form):

    class Meta:
        fields = ['lat','long']

    def save(self):
        data = self.cleaned_data
        location = UserLocation(lat=data['lat'],long=data['long'])
        location.save()