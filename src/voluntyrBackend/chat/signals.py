from django.db.models.signals import post_save
from django.dispatch import receiver

from api.models import Event
from api.signals import signal_volunteer_event_registration
from chat.models import Room, Membership
from chat.utilities import get_room_or_error

EVENT_ROOM_BASE_TITLE = "Event Chat Room for "


@receiver(post_save, sender=Event)
def new_event_receiver(sender, **kwargs):
    if kwargs['created']:
        event = kwargs['instance']
        title = EVENT_ROOM_BASE_TITLE + event.title
        room = Room.objects.create(title=title, event=event)
        Membership.objects.create(end_user=event.organization.end_user, room=room)


@receiver(signal_volunteer_event_registration)
def volunteer_event_registration_change(sender, **kwargs):
    end_user = kwargs['volunteer'].end_user
    event = Event.objects.get(id=kwargs['event_id'])
    room = get_room_or_error(event=event)
    if kwargs['attending']:
        Membership.objects.create(end_user=end_user, room=room)
    else:
        membership = Membership.objects.get(end_user=end_user, room=room)
        membership.attending = False
        membership.save(update_fields=['attending'])
