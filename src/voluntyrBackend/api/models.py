from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import EndUserManager


class EndUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = EndUserManager()

    USERNAME_FIELD = 'email'

    def get_username(self):
        return self.email


class Organization(models.Model):
    end_user = models.OneToOneField(EndUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    # TODO: Add address fields

    def __str__(self):
        return self.name


class Volunteer(models.Model):
    end_user = models.OneToOneField(EndUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    birthday = models.DateField(null=True)

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def __str__(self):
        return self.get_full_name()


class Event(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    title = models.CharField(max_length=100)
    organization = models.ForeignKey('Organization', on_delete=models.PROTECT)

    def __str__(self):
        return '%s by %s' % (self.title, self.organization)
