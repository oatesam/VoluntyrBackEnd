# TODO story-57: Delete if unused
from channels.db import database_sync_to_async

from .exceptions import ClientError
from .models import Room


@database_sync_to_async
def get_room_or_error(room_id):
    """
    Tries to get the requested a room
    """
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        raise ClientError("Room not found.")

    return room
