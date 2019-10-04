from rest_framework import generics, response, status, request

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken

from django.conf import settings

from .models import Event, Volunteer
from .serializers import EventsSerializer, ObtainTokenPairSerializer, VolunteerSerializer


class AuthCheck:
    @classmethod
    def get_user_id(cls, request):
        """
        Gets the userId from the JWT in the request
        :param request: request received by view
        :return: UserId found in this request's JWT
        """
        valid_token = cls._extract_token(request)
        return cls._get_user_id(valid_token)

    @classmethod
    def is_authorized(cls, request, required_scope):
        """
        Checks whether the JWT token in request has access to this view.
        :param request: request received by view
        :param required_scope: scope required for view. From settings.SCOPE_TYPES
        :return: True if authorized, false otherwise
        """
        valid_token = cls._extract_token(request)
        scope = cls._get_scope(valid_token)
        if scope == required_scope:
            return True
        return False

    @classmethod
    def unauthorized_response(cls):
        """
        Standard 401 response for invalid token
        :return: Response with invalid token error and HTTP 401 Status
        """
        return response.Response(data={"error": "Invalid token provided"}, status=status.HTTP_401_UNAUTHORIZED)

    @classmethod
    def _extract_token(cls, request):
        """
        Internal function to extract the JWT from request
        :param request: request received by view
        :return: Validated JWT found in request
        """
        header = request.META.get('HTTP_AUTHORIZATION').split()
        token = header[1]
        valid_token = AccessToken(token)
        return valid_token

    @classmethod
    def _get_scope(cls, token):
        """
        Internal function to extract scope from valid JWT
        :param token: valid token contained in originating request
        :return: Scope
        """
        return token.get('scope')

    @classmethod
    def _get_user_id(cls, token):
        """
        Internal function to extract userId from valid JWT
        :param token: valid token contained in originating request
        :return: UserId
        """
        return token.get('user_id')


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


class VolunteerAPIView(generics.ListCreateAPIView):
    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer






