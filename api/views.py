from django.core.validators import validate_email
from django.shortcuts import render, HttpResponse
from django.http import StreamingHttpResponse
from forms import UserCreateForm
from django.contrib.auth import authenticate, login
from models import AndroidUser
import json
from django.core import serializers
from map_methods import near_by


def create_user(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse(status=200)
        else:
            print form.error
            return StreamingHttpResponse(status=403)
    return HttpResponse('')


def login_user(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(email=email, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=403)
        return HttpResponse(status=500)
    return HttpResponse(status=200)


def check_user(request):
    if request.method == "POST":
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if not AndroidUser.objects.filter(email=email):
            if password1 and password2 and password1 == password2:
                return HttpResponse(status=200)
            return HttpResponse(status=403)
        return HttpResponse(status=403)
    return HttpResponse(status=200)


def all_users(request):
    if request.method == "GET":
        email = request.GET['email']
        user = AndroidUser.objects.get(email=email)
        excluded_users = [follower.email for follower in user.follows.all()]
        excluded_users.append(request.GET['email'])
        users_data = [user for user in AndroidUser.objects.exclude(email__in=excluded_users) if user.image.__ne__('')]
        users_data = serializers.serialize('json', users_data, use_natural_primary_keys=True)
        users_data = json.loads(users_data)
        users = {'results': []}
        for user in users_data:
            users['results'].append(user['fields'])
            user['users'] = user['fields']
            del user['fields']
        users = json.dumps(users)
        return HttpResponse(users, content_type="application/json")
    return HttpResponse(status=200)


def add_users_follow(request):
    if request.method == "POST":
        logged_email = request.POST['logged_email']
        email = request.POST['friend_email']
        followed_by = AndroidUser.objects.get(email=logged_email)
        follower = AndroidUser.objects.get(email=email)
        followed_by.add_follower(follower)
        return HttpResponse(status=200)
    return HttpResponse(status=200)


def update_location(request):
    if request.method == 'POST':
        email = request.POST['email']
        lat,lon = request.POST.get('lat', False), request.POST.get('long',False)
        if email and lat and lon:
            user = AndroidUser.objects.get(email=email)
            if user.check_location(latitude=lat,longitude=lon):
                user.add_location(latitude=lat,longitude=lon)
            nearby_friends = near_by(user, lon=lon,lat=lat)
            return HttpResponse(nearby_friends, content_type='application/json')
        return HttpResponse(status=403)
    return HttpResponse(status=403)


def all_followers(request):
    if request.method == "GET":
        email = request.GET['email']
        followers = {'results':[]}
        if email:
            user = AndroidUser.objects.get(email=email)
            friends = [friend for friend in user.follows.all()]
            locations = [friend.location for friend in friends]

            friends = serializers.serialize('json',friends, use_natural_primary_keys=True)
            friends = json.loads(friends)
            for ind, friend in enumerate(friends):
                friend['fields']['lat'], friend['fields']['long'] = str(locations[ind].lat), str(locations[ind].long)
                del friend['fields']['location']
                followers['results'].append(friend['fields'])

            return HttpResponse(json.dumps(followers), content_type='application/json')
        return HttpResponse(status=403, content="Dusan")
    return HttpResponse(status=403)

