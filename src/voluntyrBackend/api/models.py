from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

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

    def set_last_login(self):
        self.last_login = timezone.now()
        self.save()


class Organization(models.Model):
    end_user = models.OneToOneField(EndUser, unique=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=False)
    street_address = models.CharField(max_length=200, blank=False)
    city = models.CharField(max_length=30, blank=False)
    state = models.CharField(max_length=20, blank=False)
    phone_number = models.CharField(max_length=100, blank=False)
    organization_motto = models.CharField(max_length=200)

    # TODO: Add address fields - DONE
    # TODO: Consider potential useful fields

    def __str__(self):
        return self.name


class Volunteer(models.Model):
    end_user = models.OneToOneField(EndUser, unique=True, on_delete=models.CASCADE)
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
    date = models.DateField()
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    organization = models.ForeignKey('Organization', on_delete=models.PROTECT)
    volunteers = models.ManyToManyField(Volunteer, blank=True)

    # TODO: Consider potential useful fields

    def __str__(self):
        return '%s by %s' % (self.title, self.organization)
