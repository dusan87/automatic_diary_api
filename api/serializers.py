from __future__ import absolute_import

# django
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

# rest framework
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# project
from .models import (AndroidUser, Location, UsersLocations, UsersInteractions)
from api import consts


# TODO: Create dynamic fields serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AndroidUser
        fields = ('id', 'username', 'name',
                  'phone', 'country', 'city',
                  'image', 'gender', 'birth_day',)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'lng', 'lat')


class UserLocationsSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    user = UserSerializer()

    class Meta:
        model = UsersLocations
        fields = ('created_at', 'location', 'user')


class UsersInteractionsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    following = UserSerializer()
    location = LocationSerializer()

    class Meta:
        model = UsersInteractions
        fields = ('created_at', 'type', 'user', 'following', 'location')


class InteractionsSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        type_ = data.get('type')
        following_username = data.get('following_username')
        phone = data.get('phone')
        lat = data.get('lat')
        lng = data.get('lng')

        if not type_:
            raise ValidationError({
                'type': 'This field is required'
            })

        if type_ not in dict(consts.INTERACTIONS):
            raise ValidationError({
                'type': 'This field must have one of next values (call, sms, physical).'
            })

        if not following_username and type_ == consts.PHYSICAL:
            raise ValidationError({
                'following_username': 'This field is required in case type is physical.'
            })

        if following_username:
            try:
                validate_email(following_username)
            except DjangoValidationError:
                raise ValidationError({
                    'following_username': 'This field has invalid username email format.'
                })

        if not phone and type_ in (consts.CALL, consts.SMS):
            raise ValidationError({
                'phone': 'This field is required in case type is either call or sms.'
            })

        if not lat:
            raise ValidationError({
                'lat': 'This field is required.'
            })

        if not lng:
            raise ValidationError({
                'lng': 'This field is required.'
            })

        if not (-180.00 < float(lat) < 180.00):
            raise ValidationError({
                'lat': "This field must be a value between (-180.00,180.00)."
            })

        if not (-180.00 < float(lng) < 180.00):
            raise ValidationError({
                'lng': "This field must be a value between (-180.00,180.00)."
            })

        validated_data = {
            'type': type_,
            'location': {
                'lat': lat,
                'lng': lng
            },
            'following': {'phone': phone} if phone else {'username': following_username}
        }

        return validated_data

    def to_representation(self, obj):

        return {
            'type': obj.type_,
            'location': {
                'lat': obj.lat,
                'lng': obj.lng
            },
            'phone': obj.phone,
            'username': obj.following_username
        }
