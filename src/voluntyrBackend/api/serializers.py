from authy.api import AuthyApiClient
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenObtainSerializer

from .models import Event, Volunteer, Organization, EndUser


authy_api = AuthyApiClient(settings.ACCOUNT_SECURITY_API_KEY)

class EventsSerializer(serializers.ModelSerializer):
    """
    Serializer to obtain events information
    """
    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'end_time', 'date', 'location', 'description', 'organization']


class ObtainTokenPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for JWT Tokens
    """

    def get_token(self, user):
        """
        Generates JWT token for user and requests SMS dual-authentication
        :param user: EndUser requesting token
        :return: Token
        """
        end_user = EndUser.objects.get(email=user)
        end_user.set_last_login()

        token = super().get_token(user)

        scope = self.get_scope(user)
        token['scope'] = scope

        authy_id = end_user.authy_id
        authy_api.users.request_sms(authy_id, {'force': True})

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


class ObtainSocialTokenPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for Social Token Pairs
    """

class ObtainDualAuthSerializer(TokenObtainPairSerializer):
    """
    Serializer for Dual Auth Tokens
    """


class EndUserSerializer(serializers.ModelSerializer):
    """
    Serializer for an EndUser instance
    """
    class Meta:
        model = EndUser
        fields = ['email']


class VolunteerSerializer(serializers.ModelSerializer):
    """
    Serializer for Volunteers
    """
    class Meta:
        model = Volunteer
        fields = ['first_name', 'last_name', 'phone_number', 'birthday', 'end_user']


class VolunteerEventsSerializer(serializers.ModelSerializer):
    """
    Serializer for events presented to volunteers. Shows details meant only for volunteers.
    """

    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'end_time', 'date', 'location', 'description', 'organization']

    organization = serializers.StringRelatedField()


class VolunteerSearchOrganizationHelperSerializer(serializers.ModelSerializer):
    """
    Helper serializer to add organization's name and id to SearchEventsSerializer
    """
    class Meta:
        model = Organization
        fields = ['id', 'name', 'rating', 'raters']


class SearchEventsSerializer(serializers.ModelSerializer):
    """
    Serializer for events presented to volunteers. Shows details meant only for volunteers.
    """

    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'end_time', 'date', 'location', 'description', 'organization']

    organization = VolunteerSearchOrganizationHelperSerializer(many=False)


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for organization information for app - organization dashboard
    """

    class Meta:
        model = Organization
        fields = ['name', 'street_address', 'city', 'state', 'organization_motto', 'phone_number', 'rating', 'raters']


class OrganizationEventSerializer(serializers.ModelSerializer):
    """
    Serializer for Organization to view and edit the event
    """
    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'end_time', 'date', 'location', 'description', 'volunteers']


class VolunteerOrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for volunteer's to see organization details
    """
    class Meta:
        model = Organization
        fields = ['name', 'street_address', 'city', 'state', 'organization_motto', 'phone_number', 'end_user',
                  'rating', 'raters']

    end_user = EndUserSerializer(many=False)
