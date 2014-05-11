from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import datetime
# Create your models here.


class UserLocation(models.Model):

    long = models.FloatField()
    lat = models.FloatField()

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


class AndroidUser(AbstractBaseUser):

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

    def add_location(self, latitude, longitude):
        location = UserLocation(lat=latitude,long=longitude)
        location.save()
        self.location = location
        self.save(update_fields=['location_id'])

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
