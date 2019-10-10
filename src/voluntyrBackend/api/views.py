from rest_framework import generics, status, mixins
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError


from .models import Event, Organization,Volunteer, EndUser

from .serializers import EventsSerializer, ObtainTokenPairSerializer, OrganizationSerializer, VolunteerSerializer, EndUserSerializer

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
    queryset = Event.objects.filter(organization_id=2)
    serializer_class = EventsSerializer

    def list(self, request, *args, **kwargs):
        if AuthCheck.is_authorized(request, settings.SCOPE_TYPES['Organization']):
            return super().list(request, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class OrganizationCreateAPIView(generics.CreateAPIView, mixins.RetrieveModelMixin):
    """
    Class View for new organization signups.
    """
    authentication_classes = []
    permission_classes = []
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def create(self, request, *args, **kwargs):
        """
        Creates a new organization with the email, password, and name provided in the POST request body.
        :return: Status 201 if the organization is created or status 409 if the email already has an EndUser
        """
        body = json.loads(str(request.body, encoding='utf-8'))
        try:
            end_user = EndUser.objects.create_user(body['email'], body['password'])
            organization = Organization.objects.create(name=body['name'], end_user_id=end_user.id)
            serializer = OrganizationSerializer(organization)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={"error": "Organization with this email already exists."},
                            status=status.HTTP_409_CONFLICT)


class OrganizationAPIView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer
    def get_object(self):
        organization_id=1
        return Organization.objects.get(id=organization_id)

class VolunteerAPIView(generics.CreateAPIView):
    """
    Class View for new volunteer signups.
    """
    authentication_classes = []
    permission_classes = []

    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer

    def create(self, request, *args, **kwargs):
        """
        Creates a new volunteer with the email, first name, last name, date of birth, and password provided in the
        POST request body.
        :return: Status 201 if the volunteer is created or status 409 if the email already has an EndUser
        """
        body = json.loads(str(request.body, encoding='utf-8'))

        try:
            end_user = EndUser.objects.create_user(body['email'], body['password'])
            volunteer = Volunteer.objects.create(first_name=body['first_name'], last_name=body['last_name'],
                                                 birthday=body['birthday'], end_user_id=end_user.id)

            serializer = VolunteerSerializer(volunteer)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={"error": "Volunteer with this email already exists."}, status=status.HTTP_409_CONFLICT)


class CheckEmailAPIView(generics.CreateAPIView):
    """
    Class View to check if an email has an associated EndUser Account.
    """
    authentication_classes = []
    permission_classes = []

    queryset = EndUser.objects.all()
    serializer_class = EndUserSerializer

    def create(self, request, *args, **kwargs):
        """
        Post endpoint to check if email has an associated EndUser Account. Email should be in the body of the post with
        an "email" key.
        :return: Status 204 if no account exists or Status 202 if an account exists.
        """
        body = json.loads(str(request.body, encoding='utf-8'))

        try:
            end_user = EndUser.objects.get(email=body['email'])
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if end_user is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_202_ACCEPTED)

