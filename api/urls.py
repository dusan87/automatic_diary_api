from __future__ import unicode_literals, absolute_import

# django
from django.conf.urls import url

# project
from . import api

urlpatterns = [
    url(r'^create_user/$', api.CreateUser.as_view()),
    url(r'^auth_user/$', api.AuthView.as_view()),
    url(r'^validate/$', api.UserValidationView.as_view()),
    url(r'^users/$', api.ListUsersView.as_view()),
    url(r'^location/$', api.LocationView.as_view()),
    url(r'^follow/(?P<pk>[0-9]+)/$', api.FollowView.as_view()),
    url(r'^interact/$', api.InteractionView.as_view()),
    url(r'^follow/(?P<pk>[0-9]+)/$', api.FollowView.as_view()),

    # Old endpoints
    url(r'^login_user/$', 'api.views.login_user'),
    url(r'^check_user/$', 'api.views.check_user'),
    url(r'^all_users/$', 'api.views.all_users'),
    url(r'^add_follower/$', 'api.views.add_users_follow'),
    url(r'^update_location/$', 'api.views.update_location'),
    url(r'^friends_locations/$', 'api.views.all_followers'),
]
