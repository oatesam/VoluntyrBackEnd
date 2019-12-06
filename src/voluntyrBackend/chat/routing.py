from django.urls import re_path, path
from chat.consumers import ExampleConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/example/$', ExampleConsumer),
    path('ws/chat/<uuid:room_id>/', ChatConsumer),
]
