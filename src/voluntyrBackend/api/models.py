from django.db import models


# Create your models here.
class Event(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    title = models.CharField(max_length=100)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)


class Organization(models.Model):
    name = models.CharField(max_length=200)
