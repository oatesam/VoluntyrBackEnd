import json

from asgiref.sync import async_to_sync

from channels.generic.websocket import WebsocketConsumer

from chat.utilities import check_type, make_group_server_message, make_group_chat_message, make_json_chat_message, make_json_server_message


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


class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None

    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'chat_%s' % str(self.room_id)

        self.user = "test user"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        """
        Example Message:
            {
                "type": "chat_message",
                "message": "this is my message"
            }
        """
        text_data_json = json.loads(text_data)

        if isinstance(text_data_json, dict):
            if 'type' in text_data_json.keys():
                if check_type(text_data_json, "chat_message"):
                    message = text_data_json['message']
                    # TODO: add message to db
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        make_group_chat_message(self.user, message)
                    )
                    self.send(text_data=make_json_server_message("delivered", "Test id"))
                else:
                    self.send(text_data=make_json_server_message("error", "Invalid message type"))
            else:
                self.send(text_data=make_json_server_message("error", "Missing type key"))
        else:
            self.send(text_data=make_json_server_message("error", "Must send json"))

    def chat_message(self, event):
        sender = event['sender']
        message = event['message']
        self.send(text_data=make_json_chat_message(sender, message))
