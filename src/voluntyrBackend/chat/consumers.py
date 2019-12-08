from asgiref.sync import async_to_sync

from channels.generic.websocket import JsonWebsocketConsumer

from api.models import EndUser
from chat.models import Room, Membership, Message


class RoomConsumer(JsonWebsocketConsumer):
    pass


class ChatConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.username = None
        self.rooms = []

    def connect(self):
        if self._is_authenticated():
            print("Connection Authenticate!")
            self.user = EndUser.objects.get(id=self.scope['user_id'])
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.username = self.user.email

            # TODO: Mark online: New Consumer? Connect each user in chat to it to get updates
            async_to_sync(self.channel_layer.group_add)(
                self.room_id,
                self.channel_name
            )

            # TODO: Send last 10 messages in room

            self.accept()
            self.send_json(make_server_message("success", self.rooms))
        else:
            print("Failed to Connect: %s" % self.scope['auth_error'])
            self.accept()
            self.send_json(make_server_message("error", self.scope['auth_error']))
            self.close(code=4001)  # AuthError Code

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_id,
            self.channel_name
        )
        self.close()

    def _get_rooms(self):
        rooms = Room.objects.filter(membership__end_user=self.user).values_list('id', flat=True)
        for room in rooms:
            self.rooms.append(str(room))

    def _connect_to_rooms(self):
        for room in self.rooms:
            async_to_sync(self.channel_layer.group_add)(
                room,
                self.channel_name
            )

    def _disconnect_from_rooms(self):
        for room in self.rooms:
            async_to_sync(self.channel_layer.group_discard)(
                room,
                self.channel_name
            )

    def receive_json(self, content, **kwargs):
        """
        Example Message:
            {
                "type": "chat_message",
                "room": "uuid,
                "message": "this is my message"
            }
        """

        if isinstance(content, dict):
            if 'type' in content.keys():
                if check_type(content, "chat_message"):
                    if 'room' in content.keys():
                        if Room.objects.filter(id=content['room']).count() > 0:
                            room = Room.objects.get(id=content['room'])
                            if 'message' in content.keys():
                                try:
                                    Membership.objects.get(room=room, end_user=self.user)
                                    room = content['room']
                                    message = content['message']
                                    # TODO: add message to db - one entry for every other member in the room

                                    async_to_sync(self.channel_layer.group_send)(
                                        room,
                                        make_chat_message(self.username, room, message)
                                    )
                                    self.send_json(content=make_server_message("sent", "Test id"))
                                except Membership.DoesNotExist:
                                    self.send_json(
                                        content=make_server_message("error", "You are not a member of this room."))
                            else:
                                self.send_json(content=make_server_message("error", "Missing message key"))
                        else:
                            self.send_json(content=make_server_message("error", "Room doesn't exist"))
                    else:
                        self.send_json(content=make_server_message("error", "Missing room key"))
                else:
                    self.send_json(content=make_server_message("error", "Invalid message type"))
            else:
                self.send_json(content=make_server_message("error", "Missing type key"))
        else:
            self.send_json(content=make_server_message("error", "Must send json"))

    def chat_message(self, event):
        sender = event['sender']
        message = event['message']
        room = event['room']
        self.send_json(content=make_chat_message(sender, room, message))

    def _is_authenticated(self):
        if hasattr(self.scope, 'auth_error'):
            return False
        if not self.scope['user_id']:
            return False
        return True


def check_type(event, t):
    return event['type'] == t


def make_chat_message(sender, room, message):
    return {
        "type": "chat_message",
        "room": room,
        "status": "",
        "sender": sender,
        "message": message,
    }


def make_server_message(status, text):
    return {
        "type": "server",
        "room": "",
        "status": status,
        "sender": "",
        "message": text,
    }
