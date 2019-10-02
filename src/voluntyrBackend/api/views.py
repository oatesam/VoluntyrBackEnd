from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken

from django.conf import settings
from django.db import IntegrityError

from .models import Event, Organization, Volunteer, EndUser
from .serializers import EventsSerializer, ObtainTokenPairSerializer, OrganizationSerializer, VolunteerSerializer

import json


class AuthCheck:
    @classmethod
    def is_authorized(cls, request, required_scope):
        """
        Checks whether the JWT token in request has access to this view.
        :param request: request received by view
        :param required_scope: scope required for view. From settings.SCOPE_TYPES
        :return: True if authorized, false otherwise
        """
        scope = cls._get_scope(request)
        if scope == required_scope:
            return True
        return False

    @classmethod
    def unauthorized_response(cls):
        """
        Standard 401 response for invalid token
        :return: Response with invalid token error and HTTP 401 Status
        """
        return Response(data={"error": "Invalid token provided"}, status=status.HTTP_401_UNAUTHORIZED)

    @classmethod
    def _get_scope(cls, request):
        """
        Internal function to extract scope from JWT token in request
        :param request: request received by view
        :return: Scope
        """
        header = request.META.get('HTTP_AUTHORIZATION').split()
        token = header[1]
        valid_token = AccessToken(token)
        return valid_token.get('scope')


class ObtainTokenPairView(TokenObtainPairView):
    """
    Class View for user to obtain JWT token
    """
    serializer_class = ObtainTokenPairSerializer


class EventsAPIView(generics.ListCreateAPIView):

    queryset = Event.objects.all()
    serializer_class = EventsSerializer

    def list(self, request, *args, **kwargs):
        if AuthCheck.is_authorized(request, settings.SCOPE_TYPES['Organization']):
            return super().list(request, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class OrganizationAPIView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def create(self, request, *args, **kwargs):
        body = json.loads(str(request.body, encoding='utf-8'))

        try:
            end_user = EndUser.objects.create_user(body['email'], body['password'])
            organization = Organization.objects.create(name=body['name'], end_user_id=end_user.id)

            serializer = OrganizationSerializer(organization)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={"error": "Organization with this email already exists."}, status=status.HTTP_409_CONFLICT)


class VolunteerAPIView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []

    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer

    def create(self, request, *args, **kwargs):
        body = json.loads(str(request.body, encoding='utf-8'))

        try:
            end_user = EndUser.objects.create_user(body['email'], body['password'])
            volunteer = Volunteer.objects.create(first_name=body['first_name'], last_name=body['last_name'],
                                                 birthday=body['birthday'], end_user_id=end_user.id)

            serializer = VolunteerSerializer(volunteer)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={"error": "Volunteer with this email already exists."}, status=status.HTTP_409_CONFLICT)

