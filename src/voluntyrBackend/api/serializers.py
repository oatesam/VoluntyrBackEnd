from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings

from .models import Event, Volunteer, Organization


class ObtainTokenPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for JWT Tokens
    """
    def get_token(self, user):
        """
        Generates JWT token for user
        :param user: EndUser requesting token
        :return: Token
        """
        token = super().get_token(user)

        scope = self.get_scope(user)
        token['scope'] = scope

        return token

    def get_scope(self, user):
        """
        Returns authorized scope for this user
        :param user: EndUser requesting token
        :return: scope from settings.SCOPE_TYPES
        """
        scope = "none"
        if Volunteer.objects.filter(end_user=user).exists():
            scope = settings.SCOPE_TYPES['Volunteer']
        elif Organization.objects.filter(end_user=user).exists():
            scope = settings.SCOPE_TYPES['Organization']
        return scope


class VolunteerSerializer(serializers.ModelSerializer):
    """
    Serializer for Volunteers
    """
    class Meta:
        model = Volunteer
        fields = ['first_name', 'last_name', 'birthday', 'end_user']


class VolunteerEventsSerializer(serializers.ModelSerializer):
    """
    Serializer for events presented to volunteers. Shows details meant only for volunteers.
    """
    class Meta:
        model = Event
        fields = ['start_time', 'end_time', 'title', 'organization']

    organization = serializers.StringRelatedField()


class EventsSerializer(serializers.ModelSerializer):
    """
    Serializer for events presented to organizations. Shows details meant to be seen by organizer of the event.
    """
    class Meta:
        model = Event
        fields = ['start_time', 'end_time', 'title', 'organization', 'volunteers']

    volunteers = serializers.StringRelatedField(many=True, read_only=True)


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for an Organization instance
    """
    class Meta:
        model = Organization
        fields = ['name']


