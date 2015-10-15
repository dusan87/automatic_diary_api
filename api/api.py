from __future__ import absolute_import

# builtins
from datetime import timedelta, datetime as dt

# django
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import login, logout
from django.http import Http404

# rest framework
from rest_framework import (generics,
                            permissions,
                            status,
                            mixins,)
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.views import APIView
from rest_framework.response import Response

# project
from .serializers import (UserSerializer,
                          UsersLocationsSerializer,
                          InteractionsSerializer,
                          PlaceSerializer)

from .models import (User,
                     UsersLocations,
                     LocationsOfInterest,
                     UsersInteractions,
                     Notifications)

from .permissions import (IsOwnerOrReadOnly, )

from .map_methods import distance, check_distance


class CreateUser(generics.CreateAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(self.request.data['password'])
        user.save()

class AuthView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if request.user is not None and request.user.is_active:
            login(request, request.user)
            return Response(UserSerializer(request.user).data, status=201)

        return Response(
            {"message": 'User is not authorized! Please, check email and password!'}, status=401)

    def delete(self, request):
        logout(request)
        return Response({
            'message': 'User has been successfully logged out.'
        })


class UserValidationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        pass1 = request.data.get('password1')
        pass2 = request.data.get('password2')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            if not pass1 or not pass2:
                return Response({
                    "message": "Password cannot be blank value!"
                }, status=403)
            elif pass1 != pass2:
                return Response({
                    "message": "Passwords do not match!"
                }, status=403)

            return Response({
                'message': 'Email and password are correct.'
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
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self, ):
        followings = [following.email for following in self.request.user.follows.all()]
        users = User.objects.exclude(email=self.request.user.email).exclude(image='').exclude(
            email__in=followings)
        return users


class FollowView(APIView):
    """
        Add following user to user's list of followers
        @param
    """

    authentication_classes = (BasicAuthentication, )
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, pk):
        """
            @pk: primary key of follower that has been followed
                 by authenticated user
        """
        try:
            following = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

        # add relationship
        user = request.user
        user.add_follower(following)

        return Response({
            'user': UserSerializer(user).data,
            'following': UserSerializer(following).data
        })


class LocationView(APIView):

    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


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

    def get_object(self, pk):

        try:
            return UsersLocations.objects.get(pk=pk)
        except UsersLocations.DoesNotExist:
            Http404

    def get_queryset(self, ):
        """
            get user's following friends current locations
        """

        assert self.request.user

        user = self.request.user
        following_locations = []
        user_followings = user.follows.all()
        for following in user_followings:
            try:
                user_location = UsersLocations.objects.filter(user=following)[:1][0]
                if self.IsUpdated(user_location.updated_at):
                    following_locations.append(user_location)
            except IndexError:
                continue

        return following_locations

    def get(self, request):
        """
        List user's followings locations
        """

        assert request.user

        followings_locations = self.get_queryset()

        return Response({
            'followings_locations': UsersLocationsSerializer(followings_locations, many=True).data,
            'followings_places': PlaceSerializer(request.user.following_places, many=True).data,
            'user_places': PlaceSerializer(request.user.my_places, many=True).data
        })

    def post(self, request):
        """
            - store user current user location,
            - give back all user's following friends current locations
        """

        followings_locations = self.get_queryset()

        data = request.data

        serializer = UsersLocationsSerializer(data=data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        location = serializer.save()

        # TODO: There are no tests for this part of code.
        # check if there is some user to notify them
        near_followings, together_with = check_distance(location, followings_locations)

        #store together interactions
        UsersInteractions.objects.bulk_create(
            [UsersInteractions(user=request.user, partner=partner, location=location, type_of='physical')
             for partner in together_with])

        # express already notified in last 24h
        for following in near_followings:
            filtered = Notifications.objects.filter(from_notified=request.user, to_notified=following,
                                         created_at__gte=dt.utcnow()-timedelta(days=1))

            # TODO: CHECK THIS
            if len(filtered):
                near_followings.pop(following)

        #mark friends as notified
        Notifications.objects.bulk_create([Notifications(from_notified=request.user, to_notified=following)
                                           for following in near_followings])

        return Response({
            'user_location': UsersLocationsSerializer(location).data,
            'any_near': 'yes' if len(near_followings) > 0 else 'no'
        }, status=status.HTTP_201_CREATED)

    def put(self, request, pk, *args, **kwargs):
        location = self.get_object(pk)
        followings_locations = self.get_queryset()

        serializer = UsersLocationsSerializer(location, data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        location = serializer.save()

        # TODO: There are no tests for this part of code.
        # check if there is some user to notify them
        near_followings, together_with = check_distance(location, followings_locations)

        #store together interactions
        UsersInteractions.objects.bulk_create(
            [UsersInteractions(user=request.user, partner=partner, location=location, type_of='physical')
             for partner in together_with])

        # express already notified in last 24h
        for following in near_followings:
            filtered = Notifications.objects.filter(from_notified=request.user, to_notified=following,
                                         created_at__gte=dt.utcnow()-timedelta(days=1))

            # TODO: CHECK THIS
            if len(filtered):
                near_followings.pop(following)

        #mark friends as notified
        Notifications.objects.bulk_create([Notifications(from_notified=request.user, to_notified=following)
                                           for following in near_followings])

        return Response({
            'user_location': UsersLocationsSerializer(location).data,
            'any_near': 'yes' if len(near_followings) > 0 else 'no'
        }, status=status.HTTP_201_CREATED)




class InteractionView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):

        assert request.data

        serializer = InteractionsSerializer(data=request.data, context={'user': request.user})

        if serializer.is_valid():
            users_interaction = serializer.save()
            return Response({
                'interaction': InteractionsSerializer(users_interaction).data
            }, status=status.HTTP_201_CREATED)

        elif 'partner' in serializer.errors:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        limit = request.query_params.get("limit", None)
        top_friends = self.request.user.get_top_friends(limit=limit)

        return Response(
            {"top_friends": [{"count": count, "friends": UserSerializer(friend).data}
                             for count,friend in top_friends]}
        )


class TopUserPlacesView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PlaceSerializer

    def get(self, request):
        limit = request.query_params.get("limit")
        top_places = request.user.get_top_places(limit=limit)
        return Response({
            "top_places": [{"count": count, "place": PlaceSerializer(place).data}
                           for count, place in top_places]
        })


class TopPlacesView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PlaceSerializer

    def get_top_places_by_interactions(self,):
        limit = self.request.query_params.get("limit")

        interactions = UsersInteractions.objects.all()
        places = LocationsOfInterest.objects.all()

        top_by_interactions = []

        for place in places:
            interaction_counter = 0
            for interaction in interactions:
                _distance = distance(place.location.lng, place.location.lat,
                                 interaction.location.lng, interaction.location.lat)

                if _distance <= 0.2:
                    interaction_counter +=1

            if interaction_counter:
                top_by_interactions.append((interaction_counter, place))

        return sorted(top_by_interactions, reverse=True)[:limit]

    def get(self, request):
        top_places_by_interactions = self.get_top_places_by_interactions()

        return Response({
            "top_places": [{"count": count, "place": PlaceSerializer(place).data}
                           for count, place in top_places_by_interactions]
        })

class PlacesView(generics.ListCreateAPIView):
    """
    By convenient we call locations of interest as 'Places'

    - List locations of interest of current user and all his followings
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PlaceSerializer

    def get_queryset(self, ):
        """
        List user places
        List user followings
        Then for each following list places and extend the list.
        """
        user = self.request.user
        user_places = user.places.all()
        following_users = user.follows.all()
        following_places = LocationsOfInterest.objects.filter(user__in=following_users)
        return user_places, following_places

    def list(self, request, **kwargs):
        user_places, following_places = self.get_queryset()

        return Response({
            'places': {
                'user_places': PlaceSerializer(user_places, many=True).data,
                'following_places': PlaceSerializer(following_places, many=True).data,
            }
        })

    def create(self, request, *args, **kwargs):
        data = request.data

        serializer = PlaceSerializer(data=data, context={'user': request.user})

        if serializer.is_valid(raise_exception=True):
            place = serializer.save()

            return Response(PlaceSerializer(place).data, status=status.HTTP_201_CREATED)


class PlaceView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = PlaceSerializer
    queryset = LocationsOfInterest.objects.all()
