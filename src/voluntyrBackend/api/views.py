from rest_framework import generics, response, status

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken

from django.conf import settings

from .models import Event
from .serializers import EventsSerializer, ObtainTokenPairSerializer


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
        return response.Response(data={"error": "Invalid token provided"}, status=status.HTTP_401_UNAUTHORIZED)

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

