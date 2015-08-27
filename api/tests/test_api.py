import consts
import pytest
from datetime import datetime as dt
from api.api import CreateUser
from api.models import AndroidUser
import base64
import json

postgres_db = pytest.mark.django_db


class TestUserCreation():

    def test_create_user_requred_fields_failure(self, rf, create_user_view, user_required_fields):

        request = rf.post('/create_user/')
        response = create_user_view(request)
        data = response.data

        for key, value in data.items():
            assert key in user_required_fields
            assert value.pop() == 'This field is required.'

    @postgres_db
    def test_create_user_invalid_email(self, rf, create_user_view, user_data):
        user_data[consts.USER_NAME] = 'anonymous'

        request = rf.post('/create_user/', user_data)
        response = create_user_view(request)

        data = response.data

        assert 'Enter a valid email address.' in data['username']

    @postgres_db
    def test_create_user(self, rf, create_user_view, user_data):

        request = rf.post('/create_user/', user_data)
        response = create_user_view(request)

        assert response.status_code == 201

        data = response.data

        assert data

        for key, value in  data.items():
            if key in consts.USER_REQUIRED_FIELDS:
                assert value


class TestUserAuth():

    @postgres_db
    def test_not_matched_user_credentials(self, client, user_base_creds_invalid, user):
        """
            User has input eiter invaild username or password.
        """
        response = client.post('/auth_user/', HTTP_AUTHORIZATION=user_base_creds_invalid)

        data = response.data

        assert response.status_code == 403
        assert data
        assert 'detail' in data.keys()
        assert data['detail'] == 'Invalid username/password.'

    @postgres_db
    def test_user_login_auth(self, client, user_base_creds, user):

        response = client.post('/auth_user/', HTTP_AUTHORIZATION=user_base_creds)

        data =  response.data

        assert response.status_code == 201
        assert data
        assert data['username'] == user.username
        assert data['first_name'] == user.first_name
        assert data['last_name'] == user.last_name
        assert data['country'] == user.country
        assert data['city'] == user.city

    @postgres_db
    def test_user_logout(self, client):
        response = client.delete('/auth_user/')

        data = response.data
        assert response.status_code == 200
        assert data
        assert 'message' in data.keys()
        assert data['message'] == 'User has been successfully logged out.'

    @postgres_db
    def test_user_already_exist(self, client, user):

        params = {
                consts.USER_NAME: 'anonymous@gmail.com',
                'password1':'pass',
                'password2':'pass'
            }

        response = client.get('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == 'User already exist!'

    @postgres_db
    def test_passwords_not_match(self, client, user):

        params = {
                consts.USER_NAME: 'anonymous1@gmail.com',
                'password1':'pass1',
                'password2':'pass2'
            }

        response = client.get('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == 'Passwords do not match!'

    @postgres_db
    def test_passwords_cannot_be_blank(self, client, user):

        params = {
                consts.USER_NAME: 'anonymous1@gmail.com',
                'password1':'',
                'password2':'pass2'
            }

        response = client.get('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == "Password cannot be blank value!"


    @postgres_db
    def test_user_validate_successfully(self, client, user):

        params = {
                consts.USER_NAME: 'anonymous1@gmail.com',
                'password1':'pass',
                'password2':'pass'
            }

        response = client.get('/validate/', params)

        data = response.data

        assert response.status_code == 200
        assert data
        assert data['message'] == 'Username and password are correct.'

    @postgres_db
    def test_two_blank_passwords(self, client, user):

        params = {
                consts.USER_NAME: 'anonymous1@gmail.com',
                'password1':'',
                'password2':''
            }

        response = client.get('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == "Password cannot be blank value!"


class TestSuggestedUsers():

    @postgres_db
    def test_not_allowed_method(self, client, user_base_creds,user):
        """
            Not allowed methods (POST, DELETE, PUT, PATCH)
        """
        response =  client.post('/users/', HTTP_AUTHORIZATION=user_base_creds)
        data = response.data

        assert response.status_code == 403
        assert 'detail' in data.keys()
        assert data['detail'] == 'You do not have permission to perform this action.'

    @postgres_db
    def test_list_users_except_current_user_and_users_without_image(self, client, user_base_creds, user, users):
        response =  client.get('/users/', HTTP_AUTHORIZATION=user_base_creds)
        data = response.data

        assert response.status_code == 200
        assert data

        assert data['count'] == 6

        for user_data in data['results']:
            assert user_data['username'] != user.username
            assert user_data['image']

    @postgres_db
    def test_follow_user(self, client, user_base_creds, user, following_user):
        url = '/follow/%i/' % following_user.pk

        response =  client.put(url, HTTP_AUTHORIZATION=user_base_creds)

        data = response.data

        assert response.status_code == 200
        assert data

        assert 'user' in data.keys()
        assert 'following' in data.keys()
        assert following_user.username == data['following']['username']
        assert user.username == data['user']['username']

        assert following_user.username in user.get_following_users()

    @postgres_db
    def test_follow_user_not_found_pk(self, client, user_base_creds, user, following_user):
        url = '/follow/%i/' % (following_user.pk + 123)
        response =  client.put(url, HTTP_AUTHORIZATION=user_base_creds)

        data = response.data
        print data

        assert response.status_code == 404
        assert 'detail' in data
        assert data['detail'] == 'Not found.'

class TestLocationView():

    """
     - Send user location in format lat,lng
     - Store user location with assgned date time
     # - Check user location with another user
     # - Get near by friends if any
     # - Check distance of near by fiends if less than 0.2km consider as they are together.
     # - Store into user interaction
    """

    @postgres_db
    def test_store_location_and_return_followings_location(self, client, user_base_creds, user):
        """
            This api call does following:
            - Service gets user location pair lat, lng and send to api
            - Storing pair (lat, lng)
            @return: user's followings most updated location and not older than 15mins. If so we not consider user as he/she has current location and we do not return their value.
        """

        param_data = {
                'lat': 43.321321129,
                'lng': 12.1982322
            }

        response = client.post('/location/', data=param_data,HTTP_AUTHORIZATION=user_base_creds)

        data = response.data

        assert response.status_code == 201

        assert data
        assert data['user_location']
        assert data['user_location']['location']

        location = data['user_location']['location']

        assert location['lat'] == param_data['lat'] and location['lng'] ==param_data['lng']
        assert user.username == data['user_location']['user']['username']

    #TODO: Make some fake fixture with older date than 15mins and check if they are not into locations list
    @postgres_db
    def test_store_user_location_and_return_followings_locations_not_older_than_15mins(self, client, user_base_creds, user, followings_locations):
        """
            Store user location and get followings(friends) current locations that are at least updated in last 15mins from request time.
        """

        param_data = {
                'lat': 43.321321129,
                'lng': 12.1982322
            }

        response = client.post('/location/', data=param_data,HTTP_AUTHORIZATION=user_base_creds)


        assert response.status_code == 201

        data = response.data
        assert data
        assert data['followings_locations']

        locations = data['followings_locations']
        time_limit = 15 * 60 # 15mins to secs
        now = dt.utcnow()

        for loc in locations:
            assert loc['user']
            assert loc['location']['lat']
            assert loc['location']['lng']
            assert loc['created_at']

            date = dt.strptime(loc['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
            assert 0 < (now - date).total_seconds() <= time_limit # lte 15mins all following locations


    @postgres_db
    def test_storing_location_that_already_exist(self, client, user_base_creds, user):

        param_data = {
                'lat': 43.321321129,
                'lng': 12.1982322
            }

        response = client.post('/location/', data=param_data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 201

        response_data = response.data


        response = client.post('/location/', data=param_data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 201

        data = response.data


        assert response_data['user_location']['location']['id'] == data['user_location']['location']['id']

    @postgres_db
    def test_user_followings_locations_updated_at_least_in_last_15mins(self, client, user_base_creds, user, followings_locations):

        response = client.get('/location/', HTTP_AUTHORIZATION=user_base_creds)


        assert response.status_code == 200

        data = response.data
        assert data
        assert data['followings_locations']

        locations = data['followings_locations']
        time_limit = 15 * 60 # 15mins to secs
        now = dt.utcnow()

        for loc in locations:
            assert loc['user']
            assert loc['location']['lat']
            assert loc['location']['lng']
            assert loc['created_at']

            date = dt.strptime(loc['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
            assert 0 < (now - date).total_seconds() <= time_limit # lte 15mins all following locations

    @postgres_db
    def test_exluding_not_active_user_followings_locations(self, client, user_base_creds,user, followings_locations, not_active_following_location):
        """
            Check if in the following locations list there is no following that has not updated location in last 15mins
            So, we consider that kind of users location as not valid and do not list it.
        """
        response = client.get('/location/', HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200

        data = response.data
        assert data
        assert data['followings_locations']

        locations = data['followings_locations']
        time_limit = 15 * 60 # 15mins to secs
        now = dt.utcnow()

        for loc in locations:
            assert loc['user']
            assert loc['user']['username']
            assert loc['user']['username'] != 'anonymous0@gmail.com'

    # @postgres_db
    # def test_retrieving_user_locations_order_by_created_at_descending(self, client, user_base_creds, user, user_locations):

        # response = client.get('/location/', HTTP_AUTHORIZATION=user_base_creds)

        # assert response.status_code == 200

        # data = response.data

        # assert data
        # assert data['locations']
        # assert len(data['locations']) == 3

        # locations = data['locations']

        # i = 0
        # while i < len(locations) - 1:
            # gt_date = dt.strptime(locations[i]['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            # lt_date = dt.strptime(locations[i + 1]['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')

            # assert gt_date > lt_date

            # i +=1
