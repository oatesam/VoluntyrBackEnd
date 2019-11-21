from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event


@receiver(post_save, sender=Event)
def edit_handler(sender, **kwargs):
    print("test")
