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


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the `fields` arg up to the superclass
        fields = kwargs.pop('fields', None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserSerializer(DynamicFieldsModelSerializer):
    follows = serializers.StringRelatedField(many=True)
    id = serializers.CharField(required=False)
    image = serializers.ImageField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'phone', 'country', 'city',
                  'image', 'gender', 'birth_day',
                  'follows')


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    lng = serializers.CharField()
    lat = serializers.CharField()

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
        updated_at = dt.utcnow()

        # we just update `updated_at` attr in update method
        if hasattr(self, 'partial') and self.partial:
            return {
                'updated_at': updated_at,
            }

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
            'updated_at': updated_at,
            'user': self.context['user']
        }

    def to_representation(self, obj):
        return {
            'location': LocationSerializer(obj.location).data,
            'created_at': obj.created_at.strftime(DATE_FORMAT),
            'updated_at': obj.updated_at.strftime(DATE_FORMAT),
            'user': UserSerializer(obj.user).data
        }

    def create(self, validated_data):
        location, _ = Location.objects.get_or_create(**validated_data.pop('location'))

        return UsersLocations.objects.create(location=location, **validated_data)

    def update(self, instance, validated_data):

        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        instance.save()
        return instance


class InteractionsSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        type_of = data.get('type')
        partner_email = data.get('partner_email')
        phone = data.get('phone')
        lat = data.get('lat')
        lng = data.get('lng')

        partner_data = {'phone': phone} if phone else {'email': partner_email}
        user = self.context['user']

        if not type_of:
            raise ValidationError({
                'type': 'This field is required'
            })

        if type_of not in dict(consts.INTERACTIONS):
            raise ValidationError({
                'type': 'This field must have one of next values (call, sms, physical).'
            })

        if not partner_email and type_of == consts.PHYSICAL:
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

        if not phone and type_of in (consts.CALL, consts.SMS):
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
            'type_of': type_of,
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
            'type': obj.type_of,
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


class PlaceSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        lat = data.get('lat')
        lng = data.get('lng')
        type_of = data.get('type')
        description = data.get('description')
        image = data.get('image', '')
        updated_at = dt.utcnow()

        if hasattr(self, 'partial') and self.partial:

            if type_of:
                del data['type']
                data.update({'type_of': type_of})

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

        if not type_of:
            raise ValidationError({
                'type': 'This field is required.'
            })

        if not description:
            raise ValidationError({
                'description': 'This field is required.'
            })

        return {
            'type_of': type_of,
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
            'id': str(obj.id),
            'type': obj.type_of,
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