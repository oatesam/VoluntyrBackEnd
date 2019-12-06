import uuid
from django.db import models
from api.models import Event


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    members = models.ManyToManyField('api.EndUser', through="Membership")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, blank=True, null=True)
    title = models.SlugField()


class Membership(models.Model):
    end_user = models.ForeignKey('api.EndUser', on_delete=models.PROTECT)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    online = models.BooleanField(default=False)
    attending = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    sender = models.ForeignKey('api.EndUser', on_delete=models.PROTECT, related_name="sender")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    read = models.ManyToManyField('api.EndUser', through='ReadMembership', related_name="read")
    delivered = models.ManyToManyField('api.EndUser', through='DeliveredMembership', related_name="delivered")


# https://docs.djangoproject.com/en/dev/topics/db/models/#extra-fields-on-many-to-many-relationships
class ReadMembership(models.Model):
    end_user = models.ForeignKey('api.EndUser', on_delete=models.PROTECT)
    message = models.ForeignKey(Message, on_delete=models.PROTECT)
    status = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)


class DeliveredMembership(models.Model):
    end_user = models.ForeignKey('api.EndUser', on_delete=models.PROTECT)
    message = models.ForeignKey(Message, on_delete=models.PROTECT)
    status = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
