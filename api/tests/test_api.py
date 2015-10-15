import consts
import pytest
import json
from datetime import datetime as dt
from api.models import (UsersInteractions,
                        LocationsOfInterest)

postgres_db = pytest.mark.django_db


class TestUserCreation():
    @postgres_db
    def test_create_user_required_fields_failure(self, rf, create_user_view, user_required_fields):

        request = rf.post('/create_user/')
        response = create_user_view(request)
        data = response.data

        for key, value in data.items():
            assert key in user_required_fields
            assert value.pop() == 'This field is required.'

    @postgres_db
    def test_create_user_invalid_email(self, rf, create_user_view, user_data):
        user_data[consts.EMAIL] = 'anonymous'

        request = rf.post('/create_user/', user_data)
        response = create_user_view(request)

        data = response.data

        assert 'Enter a valid email address.' in data['email']

    @postgres_db
    def test_create_user(self, rf, create_user_view, user_data):

        request = rf.post('/create_user/', user_data)
        response = create_user_view(request)

        assert response.status_code == 201

        data = response.data

        assert data

        for key, value in data.items():
            if key in consts.USER_REQUIRED_FIELDS:
                assert value


class TestUserAuth():
    @postgres_db
    def test_not_matched_user_credentials(self, client, user_base_creds_invalid):
        """
            User has input either invalid email or password.
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

        data = response.data

        assert response.status_code == 201
        assert data
        assert data['email'] == user.email
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
            consts.EMAIL: 'anonymous@gmail.com',
            'password1': 'pass',
            'password2': 'pass'
        }

        response = client.post('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == 'User already exist!'

    @postgres_db
    def test_passwords_not_match(self, client, user):
        params = {
            consts.EMAIL: 'anonymous1@gmail.com',
            'password1': 'pass1',
            'password2': 'pass2'
        }

        response = client.post('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == 'Passwords do not match!'

    @postgres_db
    def test_passwords_cannot_be_blank(self, client, user):
        params = {
            consts.EMAIL: 'anonymous1@gmail.com',
            'password1': '',
            'password2': 'pass2'
        }

        response = client.post('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == "Password cannot be blank value!"

    @postgres_db
    def test_user_validate_successfully(self, client, user):
        params = {
            consts.EMAIL: 'anonymous1@gmail.com',
            'password1': 'pass',
            'password2': 'pass'
        }

        response = client.post('/validate/', params)

        data = response.data

        assert response.status_code == 200
        assert data
        assert data['message'] == 'Email and password are correct.'

    @postgres_db
    def test_two_blank_passwords(self, client, user):
        params = {
            consts.EMAIL: 'anonymous1@gmail.com',
            'password1': '',
            'password2': ''
        }

        response = client.post('/validate/', params)

        data = response.data

        assert response.status_code == 403
        assert data
        assert data['message'] == "Password cannot be blank value!"


class TestSuggestedUsers():
    @postgres_db
    def test_not_allowed_method(self, client, user_base_creds, user):
        """
            Not allowed methods (POST, DELETE, PUT, PATCH)
        """
        response = client.post('/users/', HTTP_AUTHORIZATION=user_base_creds)
        data = response.data

        assert response.status_code == 405
        assert 'detail' in data.keys()
        assert data['detail'] == 'Method "POST" not allowed.'

    @postgres_db
    def test_list_users_except_current_user_and_users_without_image_and_already_followed(self, client, user_base_creds,
                                                                                         user, users):
        response = client.get('/users/', HTTP_AUTHORIZATION=user_base_creds)
        assert response.status_code == 200
        assert response.data

        data = response.data

        assert data['count'] == 6

        for user_data in data['results']:
            assert user_data['email'] != user.email
            assert user_data['image']

    @postgres_db
    def test_follow_user(self, client, user_base_creds, user, following_user):
        url = '/follow/%i/' % following_user.pk

        response = client.put(url, HTTP_AUTHORIZATION=user_base_creds)

        data = response.data

        assert response.status_code == 200
        assert data

        assert 'user' in data.keys()
        assert 'following' in data.keys()
        assert following_user.email == data['following']['email']
        assert user.email == data['user']['email']

        assert following_user.email in user.get_following_users()

    @postgres_db
    def test_follow_user_not_found_pk(self, client, user_base_creds, following_user):
        url = '/follow/%i/' % (following_user.pk + 123)
        response = client.put(url, HTTP_AUTHORIZATION=user_base_creds)

        data = response.data
        print data

        assert response.status_code == 404
        assert 'detail' in data
        assert data['detail'] == 'Not found.'


class TestLocationView():
    @postgres_db
    def test_store_location_and_return_followings_location(self, client, user_base_creds, user):
        """
            This api call does following:
            - Service gets user location pair lat, lng and send to api
            - Storing pair (lat, lng)
            @return: user's followings most updated location and not older than 15mins.
            If so we not consider user as he/she has current location and we do not return their value.
        """

        param_data = {
            'lat': 43.321321129,
            'lng': 12.1982322
        }

        response = client.post('/location/', data=param_data, HTTP_AUTHORIZATION=user_base_creds)

        data = response.data

        assert response.status_code == 201

        assert data
        assert data['user_location']
        assert data['user_location']['location']

        location = data['user_location']['location']

        assert location['lat'] == str(param_data['lat']) and location['lng'] == str(param_data['lng'])
        assert user.email == data['user_location']['user']['email']

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

    # @postgres_db
    # def test_store_user_location_and_return_followings_locations_not_older_than_15mins(self, client, user_base_creds,
    #                                                                                    user, followings_locations):
    #     """
    #         Store user location and get followings(friends) current locations that are at least updated in last 15mins
    #         from request time.
    #     """
    #
    #     param_data = {
    #         'lat': 43.321321129,
    #         'lng': 12.1982322
    #     }
    #
    #     response = client.post('/location/', data=param_data, HTTP_AUTHORIZATION=user_base_creds)
    #
    #     assert response.status_code == 201
    #
    #     data = response.data
    #     assert data
    #     assert data['followings_locations']
    #
    #     locations = data['followings_locations']
    #     time_limit = 15 * 60  # 15mins to secs
    #     now = dt.utcnow()
    #
    #     for loc in locations:
    #         assert loc['user']
    #         assert loc['location']['lat']
    #         assert loc['location']['lng']
    #         assert loc['created_at']
    #
    #         date = dt.strptime(loc['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
    #         assert 0 < (now - date).total_seconds() <= time_limit  # lte 15mins all following locations

    @postgres_db
    def test_user_followings_locations_updated_at_least_in_last_15mins(self, client, user_base_creds, user,
                                                                       followings_locations):

        response = client.get('/location/', HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200

        data = response.data
        assert data
        assert data['followings_locations']

        locations = data['followings_locations']
        time_limit = 15 * 60  # 15mins to secs
        now = dt.utcnow()

        for loc in locations:
            assert loc['user']
            assert loc['location']['lat']
            assert loc['location']['lng']
            assert loc['created_at']

            date = dt.strptime(loc['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
            assert 0 < (now - date).total_seconds() <= time_limit  # lte 15mins all following locations

    @postgres_db
    def test_excluding_not_active_user_followings_locations(self, client, user_base_creds, user, followings_locations,
                                                            not_active_following_location):
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
        time_limit = 15 * 60  # 15mins to secs
        now = dt.utcnow()

        for loc in locations:
            assert loc['user']
            assert loc['user']['email']
            assert loc['user']['email'] != 'anonymous0@gmail.com'
            assert loc['created_at']
            assert not (now - dt.strptime(loc['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')).total_seconds() > time_limit

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

    @postgres_db
    def test_update_user_location(self, client, user_base_creds, user, user_locations):
        user_location_id = user_locations[0].id

        response = client.put('/location/%i/' % user_location_id, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200
        assert response.data

        data = response.data

        assert data['id'] == str(user_location_id)

class TestUsersInteractions():
    """
        Interaction can be achieved with three types of interactions:
        - (CALL, SMS, Physical)
        - Required fields are (type, location, interactor_email?,phone?)
        - Interactor email is required when type is Physical
        - Phone is required in case that type is either CALL or SMS
        - If we don't match ordered phone number we just avoid creation
    """

    @postgres_db
    def test_storing_users_interaction_call_fail_without_number_param(self, client, user_base_creds, user):
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.CALL],
            'phone': '',
            'lat': 43.31231,
            'lng': -34.00122,
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        data = response.data

        assert 'phone' in data.keys()
        assert data['phone'] == 'This field is required in case type is either call or sms.'

    @postgres_db
    def test_storing_users_interaction_sms_fail_without_number_param(self, client, user_base_creds, user):
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.SMS],
            'phone': '',
            'lat': 43.31231,
            'lng': -34.00122
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        data = response.data

        assert 'phone' in data.keys()
        assert data['phone'] == 'This field is required in case type is either call or sms.'

        # TODO: Set this test case into proper format, it doesnt work as I expect
        # @postgres_db
        # def test_storing_sms_users_interaction_wrong_number_format(self, client, user_base_creds, user):

        # interactions = dict(consts.INTERACTIONS)
        # data = {
        # 'type': interactions[consts.SMS],
        # 'phone':'38164159195a',
        # 'lat': 43.31231,
        # 'lng': -34.00122
        # }

        # response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        # import pdb;pdb.set_trace()
        # assert response.status_code == 400
        # assert hasattr(response, 'data')

        # data = response.data

        # assert 'phone' in data.keys()
        # assert data['phone'] == 'This field must be a numeric.'

    @postgres_db
    def test_storing_users_interactions_fail_with_invalid_following_email_format(self, client, user_base_creds, user):
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.PHYSICAL],
            'partner_email': 'anonymous',
            'lat': 43.31231,
            'lng': -34.00122
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        assert hasattr(response, 'data')

        data = response.data
        assert data['partner_email']
        assert data['partner_email'] == 'This field has invalid email format.'

    @postgres_db
    def test_without_email_and_phone_params_user_interaction_fails_on_phone_param(self, client, user_base_creds, user):
        """
        Request params data without partner_email and phone number.
        It should complaint for phone param since the type of interaction is call/sms.
        """
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.CALL],
            'lat': 43.31231,
            'lng': -34.00122
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        assert response.data
        assert response.data['phone'] == 'This field is required in case type is either call or sms.'

    @postgres_db
    def test_without_location_param_user_interaction_fails(self, client, user_base_creds, user, following_user):
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.PHYSICAL],
            'partner_email': following_user.email,
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        assert response.data
        assert response.data['lat'] == 'This field is required.'

    @postgres_db
    def test_type_of_interaction_doesnt_match_available_chooses(self, client, user_base_creds, following_user):
        data = {
            'type': "Wrong",
            'partner_email': following_user.email,
            'lat': -43.023131,
            'lng': 43.1321321
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        assert response.data
        assert response.data['type'] == 'This field must have one of next values (call, sms, physical).'

    @postgres_db
    def test_storing_users_interaction_physical(self, client, user_base_creds, user, following_email, following):
        # number of interactions between users before request
        interactions_no_before = len(UsersInteractions.objects.filter(user=user, partner=following))

        interactions = dict(consts.INTERACTIONS)
        data = {
            'partner_email': following_email,
            'type': interactions[consts.PHYSICAL],
            'lat': 43.31231,
            'lng': -34.00122,
            'phone': ''
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 201
        assert isinstance(response.data, dict)

        data = response.data
        assert data['interaction']
        assert data['interaction']['user']
        assert data['interaction']['created_at']
        assert data['interaction']['location']
        assert data['interaction']['type'] == interactions[consts.PHYSICAL]

        interactions_no_after = len(UsersInteractions.objects.filter(user=user, partner=following))

        # number of interactions should be increase for one
        assert interactions_no_before + 1 == interactions_no_after

    @postgres_db
    def test_storing_call_users_interaction(self, client, user_base_creds, user, following_user):
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.CALL],
            'phone': following_user.phone,
            'lat': 43.31231,
            'lng': -34.00122
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 201
        assert hasattr(response, 'data')

        data = response.data
        assert data
        assert data['interaction']
        assert data['interaction']['user']
        assert data['interaction']['partner']
        assert data['interaction']['created_at']
        assert data['interaction']['location']
        assert data['interaction']['type'] and data['interaction']['type'] == consts.CALL
        assert user.is_following(**{
            'id': data['interaction']['partner']['id']
        })

    @postgres_db
    def test_skip_storing_call_users_interaction(self, client, user_base_creds, user, user_with_image):
        """
        There is a user with passed number, but the user passed number is not followed by the user/person who has been called.
        We just keep tracking interaction between following users.
        """
        interactions = dict(consts.INTERACTIONS)
        data = {
            'type': interactions[consts.CALL],
            'phone': user_with_image.phone,
            'lat': 43.31231,
            'lng': -34.00122
        }

        response = client.post('/interact/', data=data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 404
        assert hasattr(response, 'data')

        data = response.data
        assert data
        assert data['partner'] == "There is no such a email or phone number of user's followings."

    @postgres_db
    def test_filter_top_n_spend_time_With_friend(self, client, user_base_creds, user, interactions):

        params = {"type": "top_friends"}
        response = client.get('/interact/', data=params, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200
        assert response.data

        assert 'top_friends' in response.data

class TestTopPlaces():

    @postgres_db
    def test_top_user_places(self, client, user_base_creds, user, user_places):
        response = client.get('/top_user_places/', HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200
        assert response.data

        assert 'top_places' in response.data

    @postgres_db
    def test_top_places(self, client, user_base_creds, user, user_places):
        response = client.get('/top_places/')

        assert response.status_code == 200
        assert response.data

        assert 'top_places' in response.data

class TestLocationsOfInterest():
    # creation
    @postgres_db
    def test_create_location_fails_required_params(self, client, user_base_creds, user, place_image, users, ):
        request_data = {
            'lat': -43.341431,
            'lng': 20.231123,
            'description': 'There is amazing view on Pariz.',
            'image': place_image,
        }

        response = client.post('/places/', data=request_data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 400
        assert response.data

        assert response.data['type'] == 'This field is required.'

        @postgres_db
        def test_create_location_with_default_image_if_there_is_no_uploaded_image_sent(self, client, user_base_creds,
                                                                                       user, place_image):
            request_data = {
                'lat': -43.341431,
                'lng': 20.231123,
                'type': 'climbing',
                'description': 'There is amazing view on Pariz.',
                'image': place_image
            }

            response = client.post('/places/', data=request_data, HTTP_AUTHORIZATION=user_base_creds)

            assert response.status_code == 201
            assert response.data

            data = response.data
            assert data['id']
            assert data['type'] == request_data['type']
            assert data['image']
            assert data['description']
            assert data['created_at']
            assert data['updated_at']
            assert data['location']['lat']
            assert data['location']['lng']

    @postgres_db
    def test_create_place(self, client, user_base_creds, user, place_image):

        request_data = {
            'lat': -43.341431,
            'lng': 20.231123,
            'type': 'enjoying',
            'description': 'There is amazing view on Pariz.',
            'image': place_image
        }

        response = client.post('/places/', data=request_data, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 201
        assert response.data
        data = response.data

        assert data['id']
        assert data['type'] == request_data['type']
        assert data['image']
        assert data['description']
        assert data['created_at']
        assert data['updated_at']
        assert data['location']['lat']
        assert data['location']['lng']

    # Get resources
    @postgres_db
    def test_get_place(self, client, user_base_creds, place):
        url = '/place/%i/' % place.id

        response = client.get(url, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200
        assert response.data

        data = response.data

        assert data['id'] == str(place.id)
        assert data['type']
        assert data['image']
        assert data['description']
        assert data['created_at']
        assert data['updated_at']
        assert data['location']['lat']
        assert data['location']['lng']

    @postgres_db
    def test_get_places(self, client, user_base_creds, user, user_places, locations):
        """
            Get all user posted places and his followings places
        :type locations: list
        """
        response = client.get('/places/', HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 200
        assert response.data

        assert response.data['places']
        assert 'user_places' in response.data['places']
        assert 'following_places' in response.data['places']

        user_places = response.data['places']['user_places']
        followings_places = response.data['places']['following_places']

        assert len(user_places) > 0

        # it's because I set fixture to create for all fixture locations places for all users
        # so, logic user's followings multipli by lenght of locations(places)
        assert len(followings_places) == len(user.follows.all()) * len(locations)

        for u_place in user_places:
            assert u_place['id']
            assert u_place['type']
            assert u_place['image']
            assert u_place['description']
            assert u_place['created_at']
            assert u_place['updated_at']
            assert u_place['location']['lat']
            assert u_place['location']['lng']

        for f_place in followings_places:
            assert f_place['id']
            assert f_place['type']
            assert f_place['image']
            assert f_place['description']
            assert f_place['created_at']
            assert f_place['updated_at']
            assert f_place['location']['lat']
            assert f_place['location']['lng']

    # Upgrade
    @postgres_db
    def test_edit_type_of_location(self, client, user_base_creds, place):

        url = '/place/{}/'.format(place.id)

        request_data = {
            'type': 'clubbing',
            'description': 'This is a good club at the heart of Sidney.',
        }

        response = client.patch(url, data=json.dumps(request_data), HTTP_AUTHORIZATION=user_base_creds,
                                content_type='application/json')

        assert response.status_code == 200
        assert response.data

        data = response.data

        assert data['id']
        assert data['type'] == request_data['type']
        assert data['image']
        assert data['description'] == request_data['description']
        assert data['created_at']
        assert data['updated_at']
        assert data['location']['lat']
        assert data['location']['lng']

    @postgres_db
    def test_edit_location_of_place(self, client, user_base_creds, place):

        url = '/place/%i/' % place.id

        request_data = {
            'type': 'clubbing',
            'lat': -94.23131
        }

        response = client.patch(url, data=json.dumps(request_data), HTTP_AUTHORIZATION=user_base_creds,
                                content_type='application/json')

        assert response.status_code == 200
        assert response.data

        data = response.data

        assert data['id']
        assert data['type'] == request_data['type']
        assert data['image']
        assert data['description']
        assert data['created_at']
        assert data['updated_at']
        assert data['location']['lat'] == str(request_data['lat'])
        assert data['location']['lng']

    @postgres_db
    def test_trying_to_edit_place_that_user_is_not_owner(self, client, user_base_creds, random_place):

        """
        :type random_place: LocationsOfInterest
        """

        url = '/place/{}/'.format(random_place.id)
        request_data = {
            'type_of': 'swimming',
            'description': 'This is a good swimming club at the heart of Sidney.'
        }

        response = client.patch(url, data=json.dumps(request_data), HTTP_AUTHORIZATION=user_base_creds,
                                content_type='application/json')

        assert response.status_code == 403
        assert response.data
        assert response.data['detail']
        assert response.data['detail'] == 'You do not have permission to perform this action.'

    # Delete
    @postgres_db
    def test_delete_place(self, client, user_base_creds, place):
        assert isinstance(place.id, int)

        url = '/place/%i/' % place.id

        assert LocationsOfInterest.objects.count() == 1

        response = client.delete(url, HTTP_AUTHORIZATION=user_base_creds)

        assert response.status_code == 204

        assert not response.data

        assert LocationsOfInterest.objects.count() == 0
