from __future__ import absolute_import

from rest_framework import generics, permissions, mixins
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.views import APIView
from .serializers import UserSerializer
from .models import AndroidUser


class CreateUser(generics.CreateAPIView):

    model = AndroidUser
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class LoginUser(APIView):

    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
