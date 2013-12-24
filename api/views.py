from django.core.validators import validate_email
from django.shortcuts import render, HttpResponse
from django.http import StreamingHttpResponse
from forms import UserCreateForm
from django.contrib.auth import authenticate, login
from models import AndroidUser
import json
from django.core import serializers


def create_user(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('')
        else:
            print form.error
            return StreamingHttpResponse(status=403)
    return HttpResponse('')


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
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
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if not AndroidUser.objects.filter(username=username):
            if password1 and password2 and password1 == password2:
                return HttpResponse(status=200)
            return HttpResponse(status=403)
        return HttpResponse(status=403)
    return HttpResponse('')


def all_users(request):
    if request.method == "GET":
        users_data = [user for user in AndroidUser.objects.exclude(username=request.GET['username']) if user.image.__ne__('')]
        users_data = serializers.serialize('json', users_data, use_natural_primary_keys=True)
        users_data = json.loads(users_data)
        users = {'results': []}
        for user in users_data:
            users['results'].append(user['fields'])
            user['users'] = user['fields']
            del user['fields']
        users = json.dumps(users)
        return HttpResponse(users, content_type="application/json")
    return HttpResponse('')