from django.urls import re_path, path
from .consumers import ExampleConsumer

websocket_urlpatterns = [
    re_path(r'ws/example/$', ExampleConsumer),
]
