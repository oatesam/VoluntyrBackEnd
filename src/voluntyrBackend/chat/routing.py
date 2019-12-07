from django.urls import path
from chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/', ChatConsumer),
    path('ws/chat/<str:token>/', ChatConsumer),
]
