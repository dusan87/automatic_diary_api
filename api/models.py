from django.db import models
from django.contrib.auth.models import User, AbstractBaseUser, BaseUserManager
import datetime
# Create your models here.


class AndroidUser(AbstractBaseUser):

    class AndroidUser(AbstractBaseUser):

        MALE = 'M'
        FEMALE = 'F'
        GENDER = (
            (MALE, 'Male'),
            (FEMALE, 'Female')
        )
        username = models.EmailField(max_length=50, unique=True, db_index=True)
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
        country = models.CharField(max_length=50, default='', blank=True)
        city = models.CharField(max_length=50, default='', blank=True)
        image = models.ImageField(blank=True, upload_to='users_photo')
        gender = models.CharField(max_length=2, choices=GENDER, default=MALE, blank=True)
        birth_day = models.DateField(default=datetime.date(2013, 2, 1), blank=True)
        objects = BaseUserManager()

        def natural_key(self):
            return self.username

        USERNAME_FIELD = 'username'
        REQUIRED_FIELDS = ['first_name', 'last_name', 'birth_day']
