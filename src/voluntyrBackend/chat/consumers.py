from channels.generic.websocket import WebsocketConsumer
import json


class ExampleConsumer(WebsocketConsumer):
    def connect(self):
        print("Connect!")
        self.accept()

    def disconnect(self, code):
        print("Disconnect!")
        pass

    def receive(self, text_data=None, bytes_data=None):
        print("Received Message!")
        if text_data is not None:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            self.send(text_data=json.dumps({
                'message': message
            }))
