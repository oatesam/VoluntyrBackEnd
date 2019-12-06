from django.db.models.signals import post_save
from django.dispatch import receiver

from api.models import Event
from chat.models import Room, Membership


@receiver(post_save, sender=Event)
def new_event_receiver(sender, **kwargs):
    if kwargs['created']:
        event = kwargs['instance']
        title = "Event Chat Room for " + event.title
        room = Room.objects.create(title=title)
        Membership.objects.create(end_user=event.organization.end_user, room=room)
