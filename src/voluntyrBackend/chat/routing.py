from django.urls import path
from chat.consumers import ChatConsumer, RoomConsumer, TypingConsumer

websocket_urlpatterns = [
    path('ws/chat/', ChatConsumer),
    path('ws/chat/<str:token>/<str:room_id>/', ChatConsumer),
    path('ws/typing/<str:token>/<str:room_id>/', TypingConsumer),
    path('ws/online/<str:token>/', RoomConsumer),
]
