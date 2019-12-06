from django.shortcuts import render
from rest_framework import generics, mixins, status
from rest_framework.response import Response

from api.views import AuthCheck
from api.models import EndUser
from chat.models import Room, Membership
from chat.serializers import RoomSerializer


# Create your views here.
class ListRoomsAPIView(generics.ListCreateAPIView, AuthCheck):
    serializer_class = RoomSerializer

    def get_queryset(self):
        end_user = EndUser.objects.get(id=AuthCheck.get_user_id(self.request))
        return Room.objects.filter(membership__end_user=end_user)

    def create(self, request, *args, **kwargs):
        user1 = EndUser.objects.get(id=AuthCheck.get_user_id(request))
        user2 = EndUser.objects.get(email=request.data['email'])

        if user1 != user2:
            room = Room.objects.create()
            Membership.objects.create(end_user=user1, room=room)
            Membership.objects.create(end_user=user2, room=room)
            return Response(data={"room": str(room.id)}, status=status.HTTP_201_CREATED)
        return Response(data={"Error": "You cannot create a private chat with yourself."},
                        status=status.HTTP_400_BAD_REQUEST)
