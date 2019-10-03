from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings

from .models import Event, Volunteer, Organization, EndUser


class EventsSerializer(serializers.ModelSerializer):
    """
    Serializer to obtain events information
    """
    class Meta:
        model = Event
        fields = ['title', 'start_time', 'end_time', 'date', 'location', 'description', 'organization']


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
        end_user = EndUser.objects.get(email=user)
        end_user.set_last_login()

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


class EndUserSerializer(serializers.ModelSerializer):
    """
    Serializer for an EndUser instance
    """
    class Meta:
        model = EndUser
        fields = ['email']


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for an Organization instance
    """
    class Meta:
        model = Organization
        fields = ['name']


class VolunteerSerializer(serializers.ModelSerializer):
    """
    Serializer for a Volunteer instance
    """
    class Meta:
        model = Volunteer
        fields = ['first_name', 'last_name', 'birthday']


class OrganizationInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for organization information for app - organization dashboard
    """

    class Meta:
        model = Organization
        fields = ['name', 'street_address', 'city', 'state', 'organization_motto', 'phone_number']
