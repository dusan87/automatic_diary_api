import pytest
import consts
import base64
import random
from django.core.files import File
from api.api import CreateUser, AuthView 
from api.models import AndroidUser, Location, UserLocations
from datetime import datetime as dt
from api.views import login_user

import os

BASE_DIR = os.path.dirname(__file__)

# Api Views fixtues
@pytest.fixture
def create_user_view():
    return CreateUser.as_view()

@pytest.fixture
def auth_view():
    return AuthView.as_view()


# User's data
@pytest.fixture
def user_required_fields():
    return consts.USER_REQUIRED_FIELDS

@pytest.fixture
def user_data():
    data = {
            consts.USER_NAME: 'anonymous@gmail.com',
            consts.FIRST_NAME: 'Anon',
            consts.LAST_NAME: 'Anon',
            consts.PASSWORD:'pass',
            consts.COUNTRY: 'Serbia',
            consts.CITY: 'Belgrade',
            consts.GENDER: 'M',
        }

    return data

@pytest.fixture
def user_credentials():
    
    credentials = {
        consts.USER_NAME:'anonymous@gmail.com',
        consts.PASSWORD: 'pass'
    }

    return credentials

@pytest.fixture
def user_base_creds():
    """User credentials in format that suites rest framework authorization"""
    
    return  "Basic " + base64.b64encode('anonymous@gmail.com:pass')

@pytest.fixture
def user_base_creds_invalid():
    """User invalid credentials in format that suites rest framework authorization"""
    
    return 'Basic ' + base64.b64encode('anonymous@gmail.com:wrongpassword')


@pytest.fixture
def image_path():
    return os.path.join(BASE_DIR, 'profile.png')

@pytest.fixture
def user(user_data):
    user = AndroidUser.objects.create_user(birth_day=dt.now(), **user_data)
    return user


@pytest.fixture
def user_with_image(user_data, image_path):

    user_data[consts.USER_NAME] = 'dusanristic@elfak.rs'
    user = AndroidUser.objects.create_user(birth_day=dt.now(), **user_data)
    user.image = File(open(image_path))
    user.save()
    assert user.pk

    return user

@pytest.fixture
def users(user_data, image_path, user, user_with_image):
    
    users = [user_with_image, user]

    for i in range(20):
        user_data[consts.USER_NAME] = 'anonymous' + str(i) + '@gmail.com'
        usr = AndroidUser.objects.create_user(birth_day=dt.now(), **user_data)
        
        if i % 2 == 0: #each second user has image
            usr.image = File(open(image_path))
            usr.save()
            assert usr.pk

            if i % 4 == 0: # add follows for user
                user.add_follower(usr)

        users.append(usr)

    return users

@pytest.fixture
def following_user(user_data):

    user_data[consts.USER_NAME] = 'follower@gmail.com'
    user = AndroidUser.objects.create_user(birth_day=dt.now(), **user_data)
    
    return user

@pytest.fixture
def locations():
   
    def cord():
        return random.uniform(-180,180)
    
    locations = [Location.objects.create(lat=cord(), lng=cord()) for i in range(3)]

    return locations

@pytest.fixture
def user_locations(user,locations):
    
    user_locations = [UserLocations(user=user, location=location).save() for location in locations]
    
    return user_locations

@pytest.fixture
def followings_locations(users, locations):
    
    followings_locations = [UserLocations(user=user, location=location).save() for user in users for location in locations]
    
    return followings_locations

@pytest.fixture
def not_active_following_location(followings_locations):

    username = 'anonymous0@gmail.com'

    anon_user = AndroidUser.objects.get(username=username)

    anon_locations = UserLocations.objects.filter(user=anon_user)
    
    dates = ['2015-08-23T{0:02d}:00:00.00Z'.format(i)for i in range(len(anon_locations))]
    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        
    for i, location in enumerate(anon_locations):
        location.created_at = dt.strptime(dates[i], date_format)
        location.save()
