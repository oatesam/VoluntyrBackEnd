from django.shortcuts import render
from rest_framework import generics

from api.views import AuthCheck
from api.models import EndUser
from chat.models import Room
from chat.serializers import RoomSerializer


# Create your views here.
class ListRoomsAPIView(generics.ListAPIView, AuthCheck):
    serializer_class = RoomSerializer

    def get_queryset(self):
        end_user = EndUser.objects.get(id=AuthCheck.get_user_id(self.request))
        return Room.objects.filter(membership__end_user=end_user)
