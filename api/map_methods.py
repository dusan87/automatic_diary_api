__author__ = 'dusanristic'

# builtins
import json
from datetime import datetime
from math import radians, cos,sin,asin,sqrt

# django
from django.core.serializers import serialize

# project
from models import (UserLocation,
                    UsersInteractions,
                    AndroidUser)


def distance(lon1,lat1,lon2,lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    #conver decimal degrees to radians

    lon1, lat1,lon2,lat2 = map(radians,[float(lon1),float(lat1),float(lon2),float(lat2)])

    #haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c

    return km


def interaction(user, friend, interact_type, location, distance_km):

    interact = UsersInteractions.objects.filter(first_user=user, second_user=friend, type=interact_type, end_time=None)

    if len(interact) == 0 and distance_km <= 0.2:
        new_interaction = UsersInteractions(first_user=user,second_user=friend, type=interact_type, location=location)
        new_interaction.save()
    elif len(interact) > 0 and distance_km <= 0.2:
        interact[0].location = location
        interact[0].save(update_fields=['location_id'])
    elif len(interact) > 0 and distance_km > 0.2:
        interact[0].end_time = datetime.now()
        interact[0].save(update_fields=['end_time'])


def near_by(user,lon,lat):

    nearby = {'results': []}

    friends = [friend for friend in user.follows.all()]
    friends = serialize('json',friends, use_natural_primary_keys=True)
    friends = json.loads(friends)
    if friends:
        for friend in friends:
            location = UserLocation.objects.get(id=friend['fields']['location'])
            distance_km = distance(lon, lat, location.long, location.lat)

            interact_type = ''
            if distance_km < 3:
                if distance_km <= 0.2:
                    interact_type = 'together'
                    friend['fields']['type'] = interact_type
                else:
                    friend['fields']['type'] = interact_type

                friend['fields']['location'] = {'lat': location.lat,'lon':location.long}
                nearby['results'].append(friend['fields'])
            #check interaction
            interaction(user,AndroidUser.objects.get(email=friend['fields']['email']), interact_type,location, distance_km)

    nearby_friend = json.dumps(nearby)
    return nearby_friend