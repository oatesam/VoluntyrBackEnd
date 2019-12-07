from django.urls import path
from chat.consumers import ChatConsumer, RoomConsumer

websocket_urlpatterns = [
    path('ws/chat/', ChatConsumer),
    path('ws/chat/<str:token>/', ChatConsumer),
    path('ws/room/<str:token>/<str:room>', RoomConsumer),
]
