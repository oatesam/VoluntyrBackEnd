import uuid

from asgiref.sync import async_to_sync

from channels.generic.websocket import JsonWebsocketConsumer
from django.utils import timezone

from api.models import EndUser
from chat.models import Room, Membership, Message, StatusMembership


class RoomConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.user = None
        self.username = None

    def connect(self):
        if self._is_authenticated():
            print("Room Connection Authenticate!")
            self.user = EndUser.objects.get(id=self.scope['user_id'])
            self.room_group_name = "online-group-room"
            self.username = self.user.email

            # TODO: Mark online: New Consumer? Connect each user in chat to it to get updates
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()

        else:
            print("Failed to Connect: %s" % self.scope['auth_error'])
            self.accept()
            self.send_json(make_server_message("error", self.scope['auth_error']))
            self.close(code=4001)  # AuthError Code

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        self.close()

    def receive_json(self, content, **kwargs):
        """
        Example Message:
            {
                "type": "online_message",
                "room": room,
                "user": "",
                "status": ""
            }
        """

        if isinstance(content, dict):
            if 'type' in content.keys():
                if check_type(content, "online_message"):
                    if 'room' in content.keys():
                        if Room.objects.filter(id=content['room']).count() > 0:
                            room = Room.objects.get(id=content['room'])
                            if 'status' in content.keys():
                                try:
                                    membership = Membership.objects.get(room=room, end_user=self.user)
                                    status = content['status']
                                    if status == "get":
                                        self.send_all_members(room)

                                    else:
                                        membership.online = (status == "online")
                                        membership.save(update_fields=["online"])
                                        async_to_sync(self.channel_layer.group_send)(
                                            self.room_group_name,
                                            self.make_online_message(self.username, str(room.id), status)
                                        )

                                except Membership.DoesNotExist:
                                    self.send_json(
                                        content=make_server_message("error", "You are not a member of this room."))
                            else:
                                self.send_json(content=make_server_message("error", "Missing status key"))
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

    def online_message(self, event):
        user = event['user']
        room = event['room']
        status = event['status']

        self.send_json(content=self.make_online_message(user, room, status))

    def send_all_members(self, room):
        for member in Membership.objects.filter(room=room, attending=True):
            self.send_json(content=self.make_online_message(str(member.end_user.email), str(room.id), str(member.online)))

        # TODO send back all member status for this group

    def make_online_message(self, user, room, status):
        return {
            'type': "online_message",
            'room': room,
            'user': user,
            'status': status
        }

    def _is_authenticated(self):
        if hasattr(self.scope, 'auth_error'):
            return False
        if not self.scope['user_id']:
            return False
        return True


class ChatConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        # self.room_group_name = None
        self.user = None
        self.username = None
        self.RECENT_MESSAGES = 10

    def connect(self):
        if self._is_authenticated():
            print("Chat Connection Authenticate!")
            self.user = EndUser.objects.get(id=self.scope['user_id'])
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.username = self.user.email

            membership = Membership.objects.get(room__id=self.room_id, end_user__email=self.username)
            membership.online = True
            membership.save()

            # TODO: Mark online: New Consumer? Connect each user in chat to it to get updates
            async_to_sync(self.channel_layer.group_add)(
                self.room_id,
                self.channel_name
            )

            # TODO: Send last 10 messages in room

            self.accept()
            self.send_json(make_server_message("success", "joined room"))

            self.recent_messages()

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

        membership = Membership.objects.get(room__id=self.room_id, end_user__email=self.username)
        membership.online = False
        membership.save()

        self.close()

    def receive_json(self, content, **kwargs):
        """
        Example Message:
            {
                "type": "chat_message",
                "room": room,
                "status": "",
                "sender": sender,
                "message": message,
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
                                    msg = Message.objects.create(
                                        room_id=uuid.UUID(room),
                                        sender=self.user,
                                        message=message
                                    )
                                    self.set_status_for_all_members(msg)

                                    async_to_sync(self.channel_layer.group_send)(
                                        room,
                                        make_chat_message(msg.id, self.username, room, message, None)
                                    )
                                    self.send_json(content=make_server_message("sent", msg.id))
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
        _id = event['id']
        sender = event['sender']
        message = event['message']
        room = event['room']

        self.send_message(_id, sender, message, room)

    def recent_messages(self):
        messages = Message.objects.filter(room__id=self.room_id)  # [:self.RECENT_MESSAGES]
        for message in messages:
            self.send_message(status=message.get_status(), **message.get_message_to_send())

    def set_status_for_all_members(self, message):
        message = Message.objects.get(id=message.id)
        members = message.room.membership_set.values_list('end_user', flat=True)
        for member in members:
            end_user = EndUser.objects.get(id=member)
            StatusMembership.objects.create(
                end_user=end_user,
                message=message,
                status=StatusMembership.SENT
            )

    def send_message(self, _id, sender, message, room, status=StatusMembership.SENT):
        self.send_json(content=make_chat_message(_id, sender, room, message, status))

        sts = StatusMembership.objects.get_or_create(message_id=_id, end_user=self.user)[0]
        sts.status = StatusMembership.DELIVERED
        sts.save(update_fields=['status'])

    def _is_authenticated(self):
        if hasattr(self.scope, 'auth_error'):
            return False
        if not self.scope['user_id']:
            return False
        return True


def check_type(event, t):
    return event['type'] == t


def make_chat_message(_id, sender, room, message, status):
    return {
        "type": "chat_message",
        "id": _id,
        "room": room,
        "status": status,
        "sender": sender,
        "message": message,
    }


def make_server_message(status, text):
    return {
        "type": "server",
        "id": "",
        "room": "",
        "status": status,
        "sender": "",
        "message": text,
    }
