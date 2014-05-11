__author__ = 'dusanristic'
from math import radians, cos,sin,asin,sqrt
from django.core.serializers import serialize
import json
from models import UserLocation

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


def near_by(user,lon,lat):

    nearby = {'results': []}

    friends = [friend for friend in user.follows.all()]
    friends = serialize('json',friends, use_natural_primary_keys=True)
    friends = json.loads(friends)
    if friends:
        for friend in friends:
            location = UserLocation.objects.get(id=friend['fields']['location'])
            distance_km = distance(lon, lat, location.long, location.lat)

            if distance_km < 3:
                friend['fields']['location'] = {'lat': location.lat,'lon':location.long}
                nearby['results'].append(friend['fields'])

    nearby_friend = json.dumps(nearby)
    return nearby_friend