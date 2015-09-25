from __future__ import absolute_import

# builtins
from datetime import datetime as dt

# django
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

# rest framework
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# project
from .models import (User,
                     Location,
                     UsersLocations,
                     UsersInteractions,
                     LocationsOfInterest)

from api import consts

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


# TODO: Create dynamic fields serializer
class UserSerializer(serializers.ModelSerializer):
    follows = serializers.StringRelatedField(many=True)
    # TODO: think about serializing places

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'phone', 'country', 'city',
                  'image', 'gender', 'birth_day',
                  'follows', 'interactions')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'lng', 'lat')


class UsersInteractionsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    partner = UserSerializer()
    location = LocationSerializer()

    class Meta:
        model = UsersInteractions
        fields = ('created_at', 'type', 'user', 'partner', 'location')


class UsersLocationsSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        lat = data.get('lat')
        lng = data.get('lng')

        if not lat:
            raise ValidationError({
                'lat': 'This field is required.'
            })

        if not lng:
            raise ValidationError({
                'lng': 'This field is required.'
            })

        return {
            'location': {
                'lat': lat,
                'lng': lng
            },
            'user': self.context['user']
        }

    def to_representation(self, obj):
        return {
            'location': LocationSerializer(obj.location).data,
            'created_at': obj.created_at.strftime(DATE_FORMAT),
            'user': UserSerializer(obj.user).data
        }

    def create(self, validated_data):
        location, _ = Location.objects.get_or_create(**validated_data.pop('location'))

        return UsersLocations.objects.create(location=location, **validated_data)

    def update(self, instance, validated_data):
        pass


class InteractionsSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        type_ = data.get('type')
        partner_email = data.get('partner_email')
        phone = data.get('phone')
        lat = data.get('lat')
        lng = data.get('lng')

        partner_data = {'phone': phone} if phone else {'email': partner_email}
        user = self.context['user']

        if not type_:
            raise ValidationError({
                'type': 'This field is required'
            })

        if type_ not in dict(consts.INTERACTIONS):
            raise ValidationError({
                'type': 'This field must have one of next values (call, sms, physical).'
            })

        if not partner_email and type_ == consts.PHYSICAL:
            raise ValidationError({
                'partner_email': 'This field is required in case type is physical.'
            })

        if partner_email:
            try:
                validate_email(partner_email)
            except DjangoValidationError:
                raise ValidationError({
                    'partner_email': 'This field has invalid email format.'
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

        try:
            partner = user.follows.get(**partner_data)
        except User.DoesNotExist:
            raise ValidationError({
                'partner': "There is no such a email or phone number of user's followings."
            })

        validated_data = {
            'type_': type_,
            'location': {
                'lat': lat,
                'lng': lng
            },
            'partner': partner,
            'user': self.context['user']
        }

        return validated_data

    def to_representation(self, obj):
        return {
            'type': obj.type_,
            'created_at': obj.created_at.strftime(DATE_FORMAT),
            'location': LocationSerializer(obj.location).data,
            'partner': UserSerializer(obj.partner).data,
            'user': UserSerializer(obj.user).data
        }

    def create(self, validated_data):
        location, _ = Location.objects.get_or_create(**validated_data.pop('location'))

        return UsersInteractions.objects.create(location=location, **validated_data)

    def update(self, instance, validated_data):
        pass


class UserRelatedField(serializers.RelatedField):
    queryset = User.objects.all()

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return UserSerializer(value).data


class TMPPlaceSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    user = UserRelatedField()

    class Meta:
        model = LocationsOfInterest
        fields = ('id', 'type', 'description', 'image', 'updated_at', 'user', 'location', 'created_at')


class PlaceSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        lat = data.get('lat')
        lng = data.get('lng')
        type_ = data.get('type')
        description = data.get('description')
        image = data.get('image', '')
        updated_at = dt.utcnow()

        if hasattr(self, 'partial') and self.partial:

            if type_:
                del data['type']
                data.update({'type_': type_})

            if lat or lng:
                location = {'lat': data.get('lat', self.instance.location.lat),
                            'lng': data.get('lng', self.instance.location.lng)}
                data.update({'location': location})

            return data

        if not lat:
            raise ValidationError({
                'lat': 'This field is required.'
            })

        if not lng:
            raise ValidationError({
                'lng': 'This field is required.'
            })

        if not type_:
            raise ValidationError({
                'type': 'This field is required.'
            })

        if not description:
            raise ValidationError({
                'description': 'This field is required.'
            })

        return {
            'type_': type_,
            'location': {
                'lat': lat,
                'lng': lng
            },
            'user': self.context['user'],
            'updated_at': updated_at,
            'image': image,
            'description': description
        }

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'type': obj.type_,
            'description': obj.description,
            'image': obj.image.url,
            'updated_at': obj.updated_at.strftime(DATE_FORMAT),
            'created_at': obj.created_at.strftime(DATE_FORMAT),
            'location': LocationSerializer(obj.location).data,
            'user': UserSerializer(obj.user).data
        }

    def create(self, validated_data):
        location, _ = Location.objects.get_or_create(**validated_data.pop('location'))

        return LocationsOfInterest.objects.create(location=location, **validated_data)

    def update(self, instance, validated_data):

        for key, value in validated_data.items():
            if hasattr(instance, key):
                if key == 'location':
                    value, _ = Location.objects.get_or_create(**validated_data.pop('location'))

                setattr(instance, key, value)

        instance.updated_at = dt.utcnow()
        instance.save()

        return instance