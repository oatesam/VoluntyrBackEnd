import uuid
from django.db import models
from api.models import Event


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    members = models.ManyToManyField('api.EndUser', through="Membership")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, null=True, default=None)

    def get_room_name(self):
        if self.event is None:
            return "Private Chat Room"
        else:
            return "Event Chat Room for " + self.event.title


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
    status = models.ManyToManyField('api.EndUser', through="StatusMembership")


# https://docs.djangoproject.com/en/dev/topics/db/models/#extra-fields-on-many-to-many-relationships
class StatusMembership(models.Model):
    SENT = 'Sent'
    DELIVERED = 'Delivered'
    READ = 'Read'
    MESSAGE_STATUS_CHOICES = [
        (SENT, 'Sent'),
        (DELIVERED, 'Delivered'),
        (READ, 'Read')
    ]

    end_user = models.ForeignKey('api.EndUser', on_delete=models.PROTECT, editable=False)
    message = models.ForeignKey(Message, on_delete=models.PROTECT, editable=False)
    status = models.CharField(choices=MESSAGE_STATUS_CHOICES, default=SENT, max_length=10)
    timestamp = models.DateTimeField(auto_now=True, db_index=True)
