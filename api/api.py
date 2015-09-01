from __future__ import absolute_import

from django.contrib.auth import login, logout
from django.http import Http404
from django.core.validators import RegexValidator
from rest_framework import generics, permissions, mixins
from rest_framework.authentication import (BasicAuthentication, SessionAuthentication)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from datetime import datetime as dt
from api import consts
from .serializers import (UserSerializer, LocationSerializer,
                          UserLocationsSerializer, UsersInteractionsSerializer, InteractionsSerializer)
from .models import (AndroidUser, Location, UserLocations, UsersInteractions)

class CreateUser(generics.CreateAPIView):

    model = AndroidUser
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class AuthView(APIView):

    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        if request.user is not None and request.user.is_active:
            login(request, request.user)
            return Response(UserSerializer(request.user).data, status=201)

        return Response(
                {"message": 'User is not authorized! Please, check username and password!'}, status=401)

    def delete(self, request, format=None):
        logout(request)
        return Response({
            'message': 'User has been successfully logged out.'
            })


class UserValidationView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        username = request.query_params.get('username')
        pass1 = request.query_params.get('password1')
        pass2 = request.query_params.get('password2')

        try:
           user = AndroidUser.objects.get(username=username)
        except AndroidUser.DoesNotExist:
            if not pass1 or not pass2:
                return Response({
                    "message": "Password cannot be blank value!"
                }, status=403)
            elif pass1 != pass2:
                return Response({
                    "message": "Passwords do not match!"
                }, status=403)

            return Response({
                'message': 'Username and password are correct.'
            })

        return Response({
            'message': 'User already exist!'
        }, status=403)


class ListUsersView(generics.ListAPIView):
    """
    Suggestion list of potentical user's followers
          - List of all users in the system
          - Exclude the user that requests the list of users
          - Exclude users without the image
          - Exclude user's following users
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, )
    permissions_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    #TODO: Check how to format response data for Android
    def get_queryset(self,):

        followings = [following.username for following in self.request.user.follows.all()]

        users = AndroidUser.objects.exclude(username=self.request.user.username).exclude(image='').exclude(username__in=followings)
        return users

class FollowView(APIView):

    """
        Add following user to user's list of followers
        @param
    """

    authorazation_class = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self, pk):
        try:
           following = AndroidUser.objects.get(pk=pk)
        except AndroidUser.DoesNotExist:
            raise Http404

        return following

    def put(self, request, pk, format=None):
        """
            @pk: primary key of follower that has been followed
                 by authenticated user
        """
        following = self.get_queryset(pk)

        #add relationship
        user = request.user
        user.add_follower(following)

        return Response({
            'user': UserSerializer(user).data,
            'following': UserSerializer(following).data
        })

class LocationView(APIView):

    authorization_class = (SessionAuthentication, BasicAuthentication)
    permission_classes  = (permissions.IsAuthenticated,)

    def IsUpdated(self, created_at):
        """
            Checking if the creation time of the object is not older than 15mins
            @time_limit: 15mins
        """

        time_limit = 15 * 60

        try:
            created = dt.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
            dist = (dt.utcnow() - created)
            return 0 < dist.total_seconds() <= time_limit
        except TypeError:
            dist = (dt.utcnow() - created_at.replace(tzinfo=None))
            return 0 < dist.total_seconds() <= time_limit



    def get_queryset(self,):
        """
            get user's following friends current locations
        """

        assert self.request.user

        user = self.request.user
        locations = []

        for following in user.follows.all():
            try:
                user_location = UserLocations.objects.filter(user=following)[:1][0]
                if self.IsUpdated(user_location.created_at):
                    locations.append(user_location)
            except IndexError:
                continue

        return locations

    def get(self, request, format=None):
        """
        List user's followings locations
        """

        assert request.user

        followings_locations = self.get_queryset()

        return Response({
            'followings_locations': UserLocationsSerializer(followings_locations, many=True).data
        })

    def post(self, request, format=None):
        """
            - store user current user location,
            - give back all user's following friends current locations
        """

        users_location = self.get_queryset()
        data = request.data

        try:
            lat, lng = data['lat'], data['lng']
            location, _ = Location.objects.get_or_create(lat=float(lat), lng=float(lng))
            user_location = UserLocations(user=request.user, location=location)
            user_location.save()
        except KeyError:
            return Response({
                'message': 'Params lat and long are required.'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'user_location': UserLocationsSerializer(user_location).data,
            'followings_locations': UserLocationsSerializer(users_location, many=True).data
        },status=status.HTTP_201_CREATED)

class InteractionView(APIView):

    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_classes = (UsersInteractionsSerializer,)

    types = (consts.CALL, consts.SMS, consts.PHYSICAL)

    def post(self, request, format=None):

        assert request.data

        serializer = InteractionsSerializer(data=request.data)

        if serializer.is_valid():
            try:
                data = serializer.validated_data
                location, _ = Location.objects.get_or_create(**data['location'])
                following = request.user.follows.get(**data['following'])

                users_interaction = UsersInteractions(user=request.user, following=following, location=location, type=data['type'])
                users_interaction.save()

            except AndroidUser.DoesNotExist:
                return Response({
                    'message': "There is no such a username or phone number of user's followings."
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                'interaction': UsersInteractionsSerializer(users_interaction).data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
