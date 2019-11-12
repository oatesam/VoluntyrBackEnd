import json
import time

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mass_mail
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Event, Organization, Volunteer, EndUser
from .serializers import EventsSerializer, ObtainTokenPairSerializer, OrganizationSerializer, VolunteerSerializer, \
    EndUserSerializer, VolunteerEventsSerializer, OrganizationEventSerializer, VolunteerOrganizationSerializer, \
    SearchEventsSerializer


class AuthCheck:
    # TODO add getVolunteerID
    # TODO add getOrganizationID
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


class OrganizationEventsAPIView(generics.ListAPIView):
    """
    Class view to get events run by the organization in the requesting JWT
    """
    serializer_class = SearchEventsSerializer

    def get_queryset(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        organization = Organization.objects.get(end_user_id=user_id)
        org_id = organization.id
        return Event.objects.filter(Q(organization_id=org_id) & Q(start_time__gte=timezone.now()))

    def list(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Organization']):
            return super().list(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class OrganizationAPIView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer

    def get_object(self):
        if AuthCheck.is_authorized(self.request, settings.SCOPE_TYPES['Organization']):
            req = self.request
            org_id = AuthCheck.get_user_id(req)

            return Organization.objects.get(end_user_id=org_id)
        return AuthCheck.unauthorized_response()


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
            return Response(data={"error": "Volunteer with this email already exists."},
                            status=status.HTTP_409_CONFLICT)


class VolunteerEventsAPIView(generics.ListAPIView, AuthCheck):
    """
    Class View for events which a volunteer has signed up for.
    """
    serializer_class = SearchEventsSerializer

    def get_queryset(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        volunteer = Volunteer.objects.get(end_user_id=user_id)
        return Event.objects.filter(Q(volunteers__id=volunteer.id) & Q(start_time__gte=timezone.now()))

    def list(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            return super().list(req, *args, **kwargs)
        else:
            return AuthCheck.unauthorized_response()


class OrganizationSignupAPIView(generics.CreateAPIView):
    """
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

    def get_object(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        return Volunteer.objects.get(end_user_id=user_id)

    def retrieve(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            return super().retrieve(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class SearchEventsAPIView(generics.ListAPIView, AuthCheck):
    """
    Class view for returning a list of events which haven't happened yet.
    Filter events based on the url params
    url params: start_time, end_time
    """

    serializer_class = SearchEventsSerializer

    def get_queryset(self):
        """
        default return events that hasn't happend yet
        check filter before final default return
        """
        queryset = Event.objects.all()
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        if start_time is not None:
            queryset.filter(start_time__gte=start_time)
        if end_time is not None:
            queryset.filter(end_time__lte=end_time)

        return queryset.filter(start_time__gte=timezone.now())

    def list(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            return super().list(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class VolunteerEventSignupAPIView(generics.GenericAPIView, AuthCheck):
    """
    Class view for volunteers to signup for events
    """
    serializer_class = EventsSerializer

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def put(self, req, *args, **kwargs):
        """
        Endpoint to add or removed a volunteer to an event
        :param req: Request
        :return:    Returns status 400 if the event doesn't exist,
                    or status 202 if the volunteer was successfully signed up.
        """
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            user_id = AuthCheck.get_user_id(req)
            volunteer = Volunteer.objects.get(end_user_id=user_id)
            vol_id = volunteer.id

            try:
                current_event = self.get_object()
            except ObjectDoesNotExist:
                return Response(data={"Error": "Given event ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            if volunteer in current_event.volunteers.all():
                current_event.volunteers.remove(vol_id)
                current_event.save()
                return Response(data={"Success": "Volunteer has been removed from event %s" % self.kwargs['event_id']},
                                status=status.HTTP_202_ACCEPTED)
            else:
                current_event.volunteers.add(vol_id)
                current_event.save()
                return Response(data={"Success": "Volunteer has signed up for event %s" % self.kwargs['event_id']},
                                status=status.HTTP_202_ACCEPTED)

        return AuthCheck.unauthorized_response()


class OrganizationEventAPIView(generics.CreateAPIView):
    """
    Class View for organization to create new event
    """
    serializer_class = EventsSerializer

    def create(self, request, *args, **kwargs):
        """
        POST endpoint to create new event
        Receives JSON in body
        :return 201 upon successful creation
        """
        if AuthCheck.is_authorized(request, settings.SCOPE_TYPES['Organization']):
            try:
                user_id = AuthCheck.get_user_id(request)
                organization = Organization.objects.get(end_user_id=user_id)
                org_id = organization.id
                body = json.loads(str(request.body, encoding='utf-8'))
                event = Event.objects.create(start_time=body['start_time'], end_time=body['end_time'],
                                             date=body['date'],
                                             title=body['title'], location=body['location'],
                                             description=body['description'],
                                             organization_id=org_id)

                return Response(data={"Success": "Event has been created"},
                                status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(data={"Error": "Event information is invalid"},
                                status=status.HTTP_400_BAD_REQUEST)

        return AuthCheck.unauthorized_response()


# TODO: 2 classes below should be refactored into a single class
class OrganizationEventUpdateAPIView(generics.UpdateAPIView):
    """
    Class View for organization to update an event
    """
    serializer_class = OrganizationEventSerializer

    def update(self, request, *args, **kwargs):
        """
        POST endpoint to update an existing event
        """
        if AuthCheck.is_authorized(request, settings.SCOPE_TYPES['Organization']):
            try:
                user_id = AuthCheck.get_user_id(request)
                organization = Organization.objects.get(end_user_id=user_id)
                org_id = organization.id
                body = json.loads(str(request.body, encoding='utf-8'))
                event = Event.objects.get(id=body['id'], organization_id=org_id)
                event.start_time = body['start_time']
                event.end_time = body['end_time']
                event.date = body['date']
                event.title = body['title']
                event.location = body['location']
                event.description = body['description']
                event.save()
                return Response(status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return AuthCheck.unauthorized_response()


class EventDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    Class View for Organizer to view & edit the Event Details
    """
    serializer_class = OrganizationEventSerializer

    def get_object(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        organization = Organization.objects.get(end_user_id=user_id)
        org_id = organization.id
        event = Event.objects.get(id=self.kwargs['event_id'], organization_id=org_id)
        return event

    def retrieve(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Organization']):
            return super().retrieve(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class OrganizationEmailVolunteers(generics.CreateAPIView, AuthCheck):
    """
    View to event organizers to email the volunteers which have signed up for a specific event.
    """

    def create(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Organization']):
            try:
                event = self._get_event(self.kwargs['event_id'])
            except ObjectDoesNotExist:
                return Response(data={"Error": "Given event ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            organizer = Organization.objects.get(end_user__id=AuthCheck.get_user_id(req))
            if organizer.id == event.organization.id:
                body = json.loads(str(req.body, encoding='utf-8'))
                volunteer_emails = self._get_volunteer_emails(event)
                eventdate = event.date.strftime("%m/%d/%Y")
                subject = "You received a message from " + organizer.name + " for their " + event.title + \
                          " event on " + eventdate
                message = "Please find their message below: \n\n" + "From: " + organizer.name + "\nSubject: " + body[
                    'subject'] + \
                          "\nMessage: " + body['message'] + "\n\n\n\n---------------------------------------------\n" \
                          + "This email is not monitored, if you would like to respond to " + organizer.name \
                          + " about this event, you may email them at " + body['replyto'] + "."
                emails = self._make_emails(volunteer_emails, settings.DEFAULT_FROM_EMAIL, subject, message)
                send_mass_mail(emails)
                return Response(data={"Success": "Emails sent."}, status=status.HTTP_200_OK)
            return Response(data={"Unauthorized": "Requesting token does not manage this event."},
                            status=status.HTTP_401_UNAUTHORIZED)
        return AuthCheck.unauthorized_response()

    def _make_emails(self, to_emails, from_email, subject, message):
        """
        Builds a tuple of the emails to send
        :param to_emails: List of volunteer emails
        :param from_email: From email address
        :param subject: Subject of the emails
        :param message: Message of the emails
        :return: Tuple of the emails to send
        """
        emails = []
        for volunteer in to_emails:
            emails.append((subject, message, from_email, [volunteer]))
        return tuple(emails)

    def _get_event(self, event_id):
        return Event.objects.get(id=event_id)

    def _get_volunteer_emails(self, event):
        volunteers = event.volunteers.all()
        emails = []
        for volunteer in volunteers:
            emails.append(volunteer.end_user.email)
        return emails


class CheckSignupAPIView(generics.RetrieveAPIView, AuthCheck):
    """
    Class view to check if a volunteer has signed up for an event
    """

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def retrieve(self, req, *args, **kwargs):
        """
        Endpoint to check if a volunteer has signed up for an event.
        :param req: request
        :param args:
        :param kwargs: Needs to contain event_id
        :return: 200 if check Okay, and true iff the volunteer is signed up
        """
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            user_id = AuthCheck.get_user_id(req)
            volunteer = Volunteer.objects.get(end_user_id=user_id)

            try:
                current_event = self.get_object()
            except ObjectDoesNotExist:
                return Response(data={"Error": "Given event ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            if volunteer in current_event.volunteers.all():
                return Response(data={"Signed-up": "true"}, status=status.HTTP_200_OK)
            else:
                return Response(data={"Signed-up": "false"}, status=status.HTTP_200_OK)

        return AuthCheck.unauthorized_response()


class EventVolunteers(generics.ListAPIView, AuthCheck):
    """
    Class view for organizations to get a list of volunteers signed up for an event
    """

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def list(self, req, *args, **kwargs):
        """
        Returns dict with the number of volunteers and a list of dictionaries with their names
        :param req: Request
        :return: 200 if response successful, 400 if event id doesn't exist, 401 if the token is not correct
        """
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Organization']):
            try:
                event = self.get_object()
            except ObjectDoesNotExist:
                return Response(data={"Error": "Given event ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            if event.organization != Organization.objects.get(end_user__id=AuthCheck.get_user_id(req)):
                return Response(data={"Error": "This organization doesn't manage this event."},
                                status=status.HTTP_400_BAD_REQUEST)

            volunteers = event.volunteers.all()
            r_dict = {"number": len(volunteers)}

            names = []
            for volunteer in volunteers:
                names.append({"name": volunteer.first_name + " " + volunteer.last_name})
            r_dict['volunteers'] = names
            return Response(data=r_dict, status=status.HTTP_200_OK)
        return AuthCheck.unauthorized_response()


class VolunteerOrganizationAPIView(generics.ListAPIView, AuthCheck):
    """
    Class view for volunteers to view organizations
    """

    serializer_class = VolunteerOrganizationSerializer

    def get_object(self):
        return Organization.objects.get(id=self.kwargs['org_id'])

    def list(self, req, *args, **kwargs):
        """
        Returns organization in the path's details and upcoming events
        :param req:
        """
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            try:
                org = self.get_object()
            except ObjectDoesNotExist:
                return Response(data={"Error": "Organization with the given Id does not exist."},
                                status=status.HTTP_400_BAD_REQUEST)
            data = {'organization': VolunteerOrganizationSerializer(org).data}
            events = Event.objects.filter(Q(organization_id=org.id) & Q(start_time__gte=timezone.now()))
            data['events'] = EventsSerializer(events, many=True).data
            return Response(data=data, status=status.HTTP_200_OK)
        return AuthCheck.unauthorized_response()
