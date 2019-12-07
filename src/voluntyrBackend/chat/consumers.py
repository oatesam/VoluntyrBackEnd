import json

from asgiref.sync import async_to_sync

from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer

from api.models import EndUser


class ExampleConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        if text_data is not None:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            self.send(text_data=json.dumps({
                'message': message
            }))


class ChatConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.username = None

    def connect(self):
        if self._is_authenticated():
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = 'chat_%s' % str(self.room_id)

            self.user = EndUser.objects.get(id=self.scope['user_id'])
            self.username = self.user.email
            # TODO: Mark online, check if in room
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()
            self.send_json(make_server_message("Success", "Joined room"))
        else:
            self.accept()
            self.send_json(make_error_message(self.scope['auth_error']))
            # self.close(code=4001)  # AuthError Code

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive_json(self, content, **kwargs):
        """
        Example Message:
            {
                "type": "chat_message",
                "message": "this is my message"
            }
        """

        if isinstance(content, dict):
            if 'type' in content.keys():
                if check_type(content, "chat_message"):
                    message = content['message']
                    # TODO: add message to db
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        make_chat_message(self.username, message)
                    )
                    self.send_json(content=make_server_message("sent", "Test id"))
                else:
                    self.send_json(content=make_server_message("error", "Invalid message type"))
            else:
                self.send_json(content=make_server_message("error", "Missing type key"))
        else:
            self.send_json(content=make_server_message("error", "Must send json"))

    def chat_message(self, event):
        sender = event['sender']
        message = event['message']
        self.send_json(content=make_chat_message(sender, message))

    def _is_authenticated(self):
        if hasattr(self.scope, 'auth_error'):
            return False
        if not self.scope['user_id']:
            return False
        return True


def check_type(event, t):
    return event['type'] == t


def make_chat_message(sender, message):
    return {
        "type": "chat_message",
        "sender": sender,
        "message": message,
    }


def make_server_message(status, text):
    return {
        "type": "server",
        "status": status,
        "text": text,
    }


def make_error_message(error):
    return {
        "error": error,
    }
