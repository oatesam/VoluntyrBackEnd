from rest_framework import generics, status, request, mixins
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import AccessToken

from django.conf import settings
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist


from .models import Event, Organization,Volunteer, EndUser

from .serializers import EventsSerializer, ObtainTokenPairSerializer, OrganizationSerializer, VolunteerSerializer, EndUserSerializer,VolunteerEventsSerializer

import json


class AuthCheck:
    @classmethod
    def get_user_id(cls, req):
        """
        Gets the userId from the JWT in the request
        :param req: request received by view
        :return: UserId found in this request's JWT
        """
        valid_token = cls._extract_token(req)
        return cls._get_user_id(valid_token)

    @classmethod
    def is_authorized(cls, req, required_scope):
        """
        Checks whether the scope of the JWT token in req has access to this view.
        :param req: request received by view
        :param required_scope: scope required for view. From settings.SCOPE_TYPES
        :return: True if authorized, false otherwise
        """
        valid_token = cls._extract_token(req)
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
        return Response(data={"error": "Invalid token provided. Token lacks required scope."},
                        status=status.HTTP_401_UNAUTHORIZED)

    @classmethod
    def _extract_token(cls, req):
        """
        Internal function to extract the JWT from request
        :param req: request received by view
        :return: Validated JWT found in request
        """
        header = req.META.get('HTTP_AUTHORIZATION').split()
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


class OrganizationEventsAPIView(generics.ListCreateAPIView):
    """
    Class view to get events run by the organization in the requesting JWT
    """
    serializer_class = EventsSerializer

    def get_queryset(self):
        req=self.request
        user_id = AuthCheck.get_user_id(req)
        organization = Organization.objects.get(end_user_id=user_id)
        org_id = organization.id
        return Event.objects.filter(organization_id=org_id)

    def list(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Organization']):
            return super().list(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


# class OrganizationCreateAPIView(generics.CreateAPIView, mixins.RetrieveModelMixin):
#     """
#     TODO: Can this class be removed?
#     Class View for new organization signups.
#     """
#     authentication_classes = []
#     permission_classes = []
#     queryset = Organization.objects.all()
#     serializer_class = OrganizationSerializer
#
#     def create(self, request, *args, **kwargs):
#         """
#         Creates a new organization with the email, password, and name provided in the POST request body.
#         :return: Status 201 if the organization is created or status 409 if the email already has an EndUser
#         """
#         print("test")
#         body = json.loads(str(request.body, encoding='utf-8'))
#         try:
#             end_user = EndUser.objects.create_user(body['email'], body['password'])
#             print("\n\n\n\n\n\n\n\n\nBody type: ")
#             print(type(body))
#             organization = Organization.objects.create(name=body['name'], end_user_id=end_user.id)
#             serializer = OrganizationSerializer(organization)
#             return Response(data=serializer.data, status=status.HTTP_201_CREATED)
#         except IntegrityError:
#             return Response(data={"error": "Organization with this email already exists."},
#                             status=status.HTTP_409_CONFLICT)


class OrganizationAPIView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer

    # TODO: Scope protect

    def get_object(self):
        req= self.request
        org_id= AuthCheck.get_user_id(req)

        return Organization.objects.get(end_user_id=org_id)


class VolunteerSignupAPIView(generics.CreateAPIView):
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


class VolunteerEventsAPIView(generics.ListAPIView):
    """
    Class View for events which a volunteer has signed up for.
    """
    serializer_class = VolunteerEventsSerializer

    # TODO: Scope protect

    def get_queryset(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        return Event.objects.filter(volunteers__id=user_id)


class OrganizationSignupAPIView(generics.CreateAPIView):
    """
    TODO: [Frontend] Needs to ensure all fields are provided
    Class View for new organization signups.
    """
    authentication_classes = []
    permission_classes = []

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def create(self, req, *args, **kwargs):
        """
        Creates a new organization with the email, password, and name provided in the POST request body.
        :return: Status 201 if the organization is created or status 409 if the email already has an EndUser
        """
        body = json.loads(str(req.body, encoding='utf-8'))
        try:
            required = ('end_user', 'name', 'street_address', 'city', 'state', 'phone_number')
            end_user = EndUser.objects.create_user(body['email'], body['password'])

            missing_keys, body = self._check_dict(body, required, end_user)
            if len(missing_keys) > 0:
                return Response(data={"error": "Request was missing keys: " + ", ".join(missing_keys)},
                                status=status.HTTP_400_BAD_REQUEST)

            organization = Organization.objects.create(**body)
            serializer = OrganizationSerializer(organization)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={"error": "Organization with this email already exists."},
                            status=status.HTTP_409_CONFLICT)

    def _check_dict(self, data, required, end_user):
        data.pop('email', False)
        data.pop('password', False)
        data['end_user'] = end_user

        if all(k in data for k in required):
            return [], data
        else:
            missing = list(set(required) - set(data.keys()))
            return missing, None


class CheckEmailAPIView(generics.CreateAPIView):
    """
    Class View to check if an email has an associated EndUser Account.
    """
    authentication_classes = []
    permission_classes = []

    queryset = EndUser.objects.all()
    serializer_class = EndUserSerializer

    def create(self, req, *args, **kwargs):
        """
        Post endpoint to check if email has an associated EndUser Account. Email should be in the body of the post with
        an "email" key.
        :return: Status 204 if no account exists or Status 202 if an account exists.
        """
        body = json.loads(str(req.body, encoding='utf-8'))

        try:
            end_user = EndUser.objects.get(email=body['email'])
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if end_user is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_202_ACCEPTED)


class VolunteerAPIView(generics.RetrieveAPIView):
    """
    Class View for volunteer to see their account details.
    """
    serializer_class = VolunteerSerializer

    # TODO: Scope protect

    def get_object(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        return Volunteer.objects.get(end_user_id=user_id)

    def retrieve(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            return super().retrieve(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class SearchEventsAPIView(generics.CreateAPIView):
    """
    Class view for returning a list of events satisfying the search criteria in the POST data
    """
    pass


class VolunteerEventSignupAPIView(generics.GenericAPIView, AuthCheck):
    """
    Class view for volunteers to signup for events
    """
    serializer_class = EventsSerializer

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def put(self, req, *args, **kwargs):
        """
        Endpoint to add volunteer to requesting event
        :param req: Request
        :return:    Returns status 400 if the event doesn't exist,
                    or status 202 if the volunteer was successfully signed up.
        """
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            user_id = AuthCheck.get_user_id(req)

            try:
                current_event = self.get_object()
            except ObjectDoesNotExist:
                return Response(data={"Error": "Given event ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            current_event.volunteers.add(user_id)
            current_event.save()
            return Response(data={"Success": "Volunteer has signed up for event %s" % self.kwargs['event_id']},
                            status=status.HTTP_202_ACCEPTED)

        return AuthCheck.unauthorized_response()
