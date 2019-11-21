from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event


@receiver(post_save, sender=Event)
def edit_handler(sender, **kwargs):
    if not kwargs['created']:
        print("test: " + str(kwargs))

# post_save.connect(edit_handler, weak=False, dispatch_uid="event_post_save")
