from django.urls import path

from chat.views import ListRoomsAPIView

urlpatterns = [
    path('rooms/', ListRoomsAPIView.as_view()),
]
