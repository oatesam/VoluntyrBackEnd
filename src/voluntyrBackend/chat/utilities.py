# TODO story-57: Delete if unused
import json

from channels.db import database_sync_to_async
from chat.exceptions import ClientError
from chat.models import Room



def get_room_or_error(id=None, event=None):
    """
    Tries to get the requested a room
    """
    if id is None and event is None:
        raise ValueError("id and event cannot both be None!")

    try:
        if id is not None:
            room = Room.objects.get(id=id)
        else:
            room = Room.objects.get(event=event)
    except Room.DoesNotExist:
        raise ClientError("Room not found.")

    return room


def check_type(event, t):
    return event['type'] == t


def make_group_chat_message(sender, message):
    return {
        "type": "chat_message",
        "sender": sender,
        "message": message,
    }


def make_group_server_message(status, text):
    return {
        "type": "server",
        "status": status,
        "text": text,
    }


def make_json_chat_message(sender, message):
    return json.dumps(make_group_chat_message(sender, message))


def make_json_server_message(status, text):
    return json.dumps(make_group_server_message(status, text))