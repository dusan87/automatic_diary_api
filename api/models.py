from __future__ import absolute_import

# builtins
import datetime

# django
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager,
                                        PermissionsMixin)
# Create your models here.
# TODO: CREATE PROPER RELATED_NAME values FOR EACH RELATIONSHIP

# TODO: This should be just location, not user location
class UserLocation(models.Model):

    user = models.ForeignKey('User', related_name="locations")
    long = models.FloatField()
    lat = models.FloatField()
    last_update = models.DateTimeField(auto_now_add=True, null=True)


class UserManager(BaseUserManager):

    def _create_user(self, email, password, phone, **extra_fields):
        """
        Creates and saves a User with a given username(email), phone and password.
        """
        if not email:
            raise ValueError("The given email must be set.")

        email = self.normalize_email(email)
        user = self.model(email=email,
                          phone=phone,
                          **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password, phone, **extra_fields):

        return self._create_user(email, password, phone, **extra_fields)

    def create_superuser(self, email, password, phone, **extra_fields):

        return self._create_user(email, password, phone, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    MALE = 'M'
    FEMALE = 'F'

    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female')
    )

    follows = models.ManyToManyField('self', related_name="followers", symmetrical=False, help_text=_('friendship relation'))
    interactions = models.ManyToManyField('self', through='UsersInteractions', through_fields=('user', 'partner'))

    email = models.EmailField(_("email address"), max_length=50, unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=25)
    last_name = models.CharField(_("last name"), max_length=25)
    gender = models.CharField(max_length=2, choices=GENDER, default=MALE, blank=True)
    birth_day = models.DateField(_("birthday"), blank=True, null=True)

    phone = models.CharField(max_length=15, unique=True)
    country = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    image = models.ImageField(blank=True, upload_to='users_photo')

    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def natural_key(self):
        return self.email

    def __str__(self):
        return self.email

    def add_follower(self, user):
        if user not in self.follows.all():
            self.follows.add(user)

    def is_following(self, **kwargs):
        try:
            self.follows.get(**kwargs)
        except self.DoesNotExist:
            return False

        return True

    def get_following_users(self):
        return [user.email for user in self.follows.all()]

    def get_interactions(self):
        #TODO: Implement
        pass

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

            tmp = interact.second_user.email
            total_time = (interact.end_time - interact.start_time).total_seconds()

            if i + 1 < len(interactions):
                for inter in interactions[i + 1:]:
                    if inter.second_user.email == tmp and not tmp in friends:
                        total_time += (inter.end_time - inter.start_time).total_seconds()

            if not tmp in friends:
                friends.append(tmp)
                top10['results'].append({'email':tmp, 'total_time':total_time})

        del friends
        return top10

    def as_json_dict(self):
        return {
            'email': self.email,
            'first_name':self.first_name,
            'last_name': self.last_name,
            'country':self.country,
            'city': self.city,
            'birth_day': str(self.birth_day)
        }


class UsersInteractions(models.Model):

    TYPES = (
        ('physical','physical'),
        ('call','call'),
        ('sms','sms')
    )

    user = models.ForeignKey('User', related_name = 'interactor')
    partner = models.ForeignKey('User', related_name= 'partner', help_text=_('partner in interaction'))

    location = models.ForeignKey('Location', related_name='users_locations')
    type = models.CharField(max_length=25, choices=TYPES)
    created_at = models.DateTimeField(auto_now_add=True)


class Location(models.Model):
    lng = models.FloatField()
    lat = models.FloatField()

    tracked_users = models.ManyToManyField('User', through='UsersLocations')

    def __str__(self):
        return ",".join((str(self.lng),str(self.lat)))


class UsersLocations(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    user = models.ForeignKey('User', related_name='locations')
    location = models.ForeignKey('Location', related_name='users')

    class Meta:
        ordering = ['-created_at']


class LocationsOfInterest(models.Model):

    # many to one
    user = models.ForeignKey('User', related_name='places')  # TODO: check this related_name
    location = models.ForeignKey('Location', related_name='of_interests')

    type = models.CharField(max_length=50, verbose_name='Restaurants, bar, library...')
    description = models.CharField(max_length=1000)
    image = models.ImageField(upload_to='place_imgs', blank=True)

    created_at = models.DateTimeField(_("creation time"),auto_now_add=True)
    updated_at = models.DateTimeField(_("last updated"))

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.type
