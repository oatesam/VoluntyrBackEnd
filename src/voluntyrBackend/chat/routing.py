from django.urls import re_path, path
from chat.consumers import ExampleConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/example/$', ExampleConsumer),
    re_path(r'ws/chat/<uuid:room>/$', ChatConsumer),  # TODO: Pick up here: https://channels.readthedocs.io/en/latest/tutorial/part_2.html#enable-a-channel-layer
]
