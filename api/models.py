from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import datetime
# Create your models here.


# TODO: This should be just location, not user location
class UserLocation(models.Model):

    user = models.ForeignKey('AndroidUser', related_name = "user's location")
    long = models.FloatField()
    lat = models.FloatField()
    last_update = models.DateTimeField(auto_now_add=True, null=True)


# TODO: This should be Userprofile manager
class AndroidUserManager(BaseUserManager):

    def create_user(self, username,first_name=None, last_name=None, country=None, city=None, gender=None,
                    birth_day=None, password=None):

        if not username:
            raise ValueError("User must have a username")

        user = self.model(username=username, first_name=first_name,last_name=last_name,
                          country=country,city=city, gender=gender, birth_day=birth_day)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, first_name,last_name,country,city,gender,birth_day,password):

        user = self.create_user(username=username,first_name=first_name,last_name=last_name,country=country,city=city,
                                gender=gender,birth_day=birth_day,password=password)

        user.save(using=self._db)
        return user

#TODO: This should be User Profile, to be more generalized

class AndroidUser(AbstractBaseUser, PermissionsMixin):

    MALE = 'M'
    FEMALE = 'F'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female')
    )
    username = models.EmailField(max_length=50, unique=True, db_index=True, default='')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    country = models.CharField(max_length=50, default='', blank=True)
    city = models.CharField(max_length=50, default='', blank=True)
    image = models.ImageField(blank=True, upload_to='users_photo')
    gender = models.CharField(max_length=2, choices=GENDER, default=MALE, blank=True)
    birth_day = models.DateField(default=datetime.date(2013, 2, 1), blank=True)
    follows = models.ManyToManyField('self', related_name="follow", symmetrical=False)
    location = models.ForeignKey(UserLocation, null=True)
    objects = AndroidUserManager()

    def natural_key(self):
        return self.username

    def add_follower(self, user):
        if user not in self.follows.all():
            self.follows.add(user)

    def get_following_users(self):
        return [user.username for user in self.follows.all()]

    def check_location(self, latitude, longitude):
        if self.location and self.location.lat == latitude and self.location.long == longitude:
            return False
        return True

    def add_location(self, latitude, longitude):
        location = UserLocation(lat=latitude,long=longitude)
        location.save()
        self.location = location
        self.save(update_fields=['location_id'])

    def top_10_spending_time(self, period_start=datetime.datetime.utcfromtimestamp(0), period_end=datetime.datetime.now()):
        interactions = UsersInteractions.objects.filter(first_user=self, type='together',start_time__gte=period_start,
                                                        start_time__lte=period_end, end_time__isnull=False)
        top10 = {'results': []}
        friends = []
        for i, interact in enumerate(interactions):

            tmp = interact.second_user.username
            total_time = (interact.end_time - interact.start_time).total_seconds()

            if i + 1 < len(interactions):
                for inter in interactions[i + 1:]:
                    if inter.second_user.username == tmp and not tmp in friends:
                        total_time += (inter.end_time - inter.start_time).total_seconds()

            if not tmp in friends:
                friends.append(tmp)
                top10['results'].append({'username':tmp, 'total_time':total_time})

        del friends
        return top10

    def as_json_dict(self):
        return {
            'username': self.username,
            'first_name':self.first_name,
            'last_name': self.last_name,
            'country':self.country,
            'city': self.city,
            'birth_day': str(self.birth_day)
        }

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name','country','city','gender','birth_day']


class UsersInteractions(models.Model):

    type = models.CharField(max_length=50)
    first_user = models.ForeignKey(AndroidUser, related_name='first_user')
    second_user = models.ForeignKey(AndroidUser, related_name='second_user', null=True)
    location = models.ForeignKey(UserLocation)

    start_time = models.DateTimeField(auto_now_add=True,blank=True)
    end_time = models.DateTimeField(blank=True, null=True)

    phone_number = models.CharField(max_length=50,blank=True, null=True)


class Location(models.Model):
    lng = models.FloatField()
    lat = models.FloatField()

    users = models.ManyToManyField('AndroidUser', through='UserLocations')

    def __str__(self):
        return ",".join((str(self.lng),str(self.lat)))


class UserLocations(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    user = models.ForeignKey('AndroidUser')
    location = models.ForeignKey('Location')

    class Meta:
        ordering = ['-created_at']

class LocationsOfInterest(models.Model):

    type_of = models.CharField(max_length=50, verbose_name='Restaurange, bar, library...')
    decription = models.CharField(max_length=1000)
    image = models.ImageField(blank=True,upload_to='place_imgs')

    #One to many to user
    user = models.ForeignKey('AndroidUser')

    # one to one to location
    location = models.OneToOneField('Location')

    def __str__(self):
        return self.type_of
