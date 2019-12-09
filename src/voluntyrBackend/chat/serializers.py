from rest_framework import serializers
from chat.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name']

    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_room_name()
