import pytest
import consts
import base64
import random
from django.core.files import File
from api.api import CreateUser, AuthView
from api.models import (User,
                        Location,
                        UsersLocations,
                        LocationsOfInterest)
from datetime import datetime as dt

import os

BASE_DIR = os.path.dirname(__file__)

# Api Views fixtures
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
        consts.EMAIL: 'anonymous@gmail.com',
        consts.FIRST_NAME: 'Anon',
        consts.LAST_NAME: ' Anon',
        consts.PASSWORD:'pass',
        consts.COUNTRY: 'Serbia',
        consts.CITY: 'Belgrade',
        consts.GENDER: 'M',
        consts.PHONE_NUMBER: '+381645227594'
    }

    return data

@pytest.fixture
def user_credentials():

    credentials = {
        consts.EMAIL:'anonymous@gmail.com',
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
    user = User.objects.create_user(birth_day=dt.now(), **user_data)
    return user


@pytest.fixture
def user_with_image(user_data, image_path):

    user_data[consts.EMAIL] = 'dusanristic@elfak.rs'
    user_data[consts.PHONE_NUMBER] = '+381640000000'
    user = User.objects.create_user(birth_day=dt.now(), **user_data)
    user.image = File(open(image_path))
    user.save()
    assert user.pk

    return user

@pytest.fixture
def users(user_data, image_path, user, user_with_image):

    users = [user_with_image, user]

    for i in range(20):
        user_data[consts.EMAIL] = 'anonymous' + str(i) + '@gmail.com'
        user_data[consts.PHONE_NUMBER] = '+381' + str(random.randint(60,69)) + str(random.randint(0000000,9999999))
        usr = User.objects.create_user(birth_day=dt.now(), **user_data)

        if i % 2 == 0:  # each second user has image
            usr.image = File(open(image_path))
            usr.save()
            assert usr.pk

            if i % 4 == 0:  # add follows for user
                user.add_follower(usr)

        users.append(usr)

    return users

@pytest.fixture
def following_user(user,user_data):

    user_data[consts.EMAIL] = 'follower@gmail.com'
    user_data[consts.PHONE_NUMBER] = '+381650000000'
    follower = User.objects.create_user(birth_day=dt.now(), **user_data)

    user.add_follower(follower)
    return follower

@pytest.fixture
def locations():

    def cord():
        return random.uniform(-180,180)

    locations = [Location.objects.create(lat=cord(), lng=cord()) for i in range(3)]

    return locations

@pytest.fixture
def user_locations(user,locations):

    user_locations = [UsersLocations(user=user, location=location).save() for location in locations]

    return user_locations

@pytest.fixture
def followings_locations(users, locations):

    followings_locations = [UsersLocations(user=user, location=location).save() for user in users for location in locations]

    return followings_locations

@pytest.fixture
def not_active_following_location(followings_locations):

    email = 'anonymous0@gmail.com'

    anon_user = User.objects.get(email=email)

    anon_locations = UsersLocations.objects.filter(user=anon_user)

    dates = ['2015-08-23T{0:02d}:00:00.00Z'.format(i)for i in range(len(anon_locations))]
    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    for i, location in enumerate(anon_locations):
        location.created_at = dt.strptime(dates[i], date_format)
        location.save()

@pytest.fixture
def following_pk(user):
    followings_pk = [following.pk for following in user.follow.all()]

    return random.choice(followings_pk)

@pytest.fixture
def following_email():
    return 'anonymous0@gmail.com'

@pytest.fixture
def following(users):
    try:
        following = User.objects.get(email=following_email)
    except User.DoesNotExist:
        return 'There is no such a User with this email!'

    return following


# Places = Locations of Interests

def create_place(location, user, image):
    types = ('chilling', 'clubing', 'library', 'meeting')
    descriptions = ('Amazing!', "Let's get it!", "Something amazing!")

    place = LocationsOfInterest.objects.create(description=random.choice(descriptions),
                                               type_=random.choice(types),
                                               updated_at=dt.utcnow(),
                                               image=image,
                                               user=user,
                                               location=location)


    return place


@pytest.fixture
def place_image(image_path):
    return File(open(image_path))

@pytest.fixture
def place(user, locations, image_path):

    location = locations[0]
    description = 'There is amazing iceream.'
    type_of = 'chilling'
    last_update = dt.utcnow()
    image = File(open(image_path))

    place = LocationsOfInterest.objects.create(description=description,
                                               type_=type_of,
                                               updated_at=last_update,
                                               image=image,
                                               user=user,
                                               location=location)

    return place

@pytest.fixture
def user_places(user, locations, image_path):

    types = ('chilling', 'clubing', 'library', 'meeting')
    descriptions = ('Amazing!', "Let's get it!", "Something amazing!")
    image = File(open(image_path))

    def _place(location):

        place = LocationsOfInterest.objects.create(description=random.choice(descriptions),
                                               type_=random.choice(types),
                                               updated_at=dt.utcnow(),
                                               image=image,
                                               user=user,
                                               location=location)
        return place

    places = [_place(location) for location in locations]

    return places

@pytest.fixture
def users_places(locations, users, image_path):
    places = [create_place(location, user, File(open(image_path))) for user in users for location in locations]

    return places

@pytest.fixture
def random_place(users_places):
    return random.choice(users_places)
