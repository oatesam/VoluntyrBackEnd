import json
import sys
import time
import math

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mass_mail, send_mail
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from .signals import signal_volunteer_signed_up_event
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView
from authy.api import AuthyApiClient

from .models import Event, Organization, Volunteer, EndUser, Rating
from .serializers import EventsSerializer, ObtainTokenPairSerializer, OrganizationSerializer, VolunteerSerializer, \
    EndUserSerializer, OrganizationEventSerializer, VolunteerOrganizationSerializer, \
    SearchEventsSerializer, ObtainDualAuthSerializer
from .urlTokens.token import URLToken

authy_api = AuthyApiClient(settings.ACCOUNT_SECURITY_API_KEY)


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


class ObtainDualAuthView(generics.GenericAPIView):
    """
    Class View for user to obtain Dual Authentication Token
    """
    serializer_class = ObtainDualAuthSerializer

    def post(self, request, *args, **kwargs):
        """
        Validates the token provided in the
        POST request body.
        :return: Status 200 if the token is valid and 400 if invalid
        """
        body = json.loads(str(request.body, encoding='utf-8'))

        user_id = AuthCheck.get_user_id(self.request)
        end_user = EndUser.objects.get(id=user_id)
        authy_id = end_user.authy_id

        verification = authy_api.tokens.verify(authy_id, token=body['token'])

        if verification.ok():
            return Response(data={'verified': 'true'}, status=status.HTTP_200_OK)
        else:
            return Response(data={'verified': 'false'}, status=status.HTTP_400_BAD_REQUEST)



class RecoverPasswordView(generics.CreateAPIView):
    """
    View to generate an recovery code for an event. GET will return a recovery code for this user and POST will email
    the provided email a link to recover
    """
    def create(self, req, *args, **kwargs):
        try:
            body = json.loads(str(req.body, encoding='utf-8'))
            end_user = EndUser.objects.get(email=body['email'])
        except ObjectDoesNotExist:
            return Response(data={"Error": "Given user does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        full_path = HttpRequest.get_full_path(req)
        print('url generated = ', full_path, file=sys.stderr)
        email = body['email']
        subject = "Voluntyr Password Recovery Link "
        recover_code = self._generate_recover_code(end_user.id)
        message = "Please find the recovery link below. \n\n" + \
                   "\n" + "\n\n\n\n---------------------------------------------\n" \
                  + "Please do not respond to this message, as it cannot receive incoming mail.\n" + \
                   "Please contact us through our website instead, at voluntyr.com"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        return Response(data={"Success": "Emails sent."}, status=status.HTTP_200_OK)

    def _generate_recover_code(self, user_id):
        token = URLToken(data={"user_id": user_id})
        return token.get_token()

class ResetPasswordView(generics.UpdateAPIView):
    def get(self):
        return 1


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
            authy_user = authy_api.users.create(
                email=body['email'],
                phone=body['phone_number'],
                country_code=1)

            if not authy_user.ok():
                authy_id = "209891210"
                print(authy_user.errors())
            else:
                authy_id = authy_user.id

            end_user = EndUser.objects.create_user(body['email'], body['password'], authy_id)
            volunteer = Volunteer.objects.create(first_name=body['first_name'], last_name=body['last_name'],
                                                 birthday=body['birthday'], phone_number=body['phone_number'],
                                                 end_user_id=end_user.id)

            serializer = VolunteerSerializer(volunteer)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={"error": "Volunteer with this email already exists."},
                            status=status.HTTP_409_CONFLICT)


# TODO: Write tests to get single event, add to search event tests
class VolunteerEventAPIView(generics.RetrieveAPIView, AuthCheck):
    """
    Class view to return a single events to volunteers
    """
    serializer_class = SearchEventsSerializer

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def retrieve(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            return super().retrieve(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


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


class VolunteerUnratedEventsAPIView(generics.ListAPIView, AuthCheck):
    """
    Class View for past events which a volunteer has signed up for and have not been rated
    """
    serializer_class = SearchEventsSerializer

    def get_queryset(self):
        req = self.request
        user_id = AuthCheck.get_user_id(req)
        volunteer = Volunteer.objects.get(end_user_id=user_id)
        rated_events = Rating.objects.filter(Q(volunteer=volunteer)).values('event')
        return Event.objects.filter(Q(volunteers__id=volunteer.id) & Q(start_time__lt=timezone.now())) \
            .exclude(id__in=rated_events)

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
            authy_user = authy_api.users.create(
                email=body['email'],
                phone=body['phone_number'],
                country_code=1)

            if not authy_user.ok():
                authy_id = "209891210"
                print(authy_user.errors())
            else:
                authy_id = authy_user.id

            end_user = EndUser.objects.create_user(body['email'], body['password'], authy_id)

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
        default return events that hasn't happened yet
        check filter before final default return
        """
        queryset = Event.objects.all()
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        title = self.request.query_params.get('title', None)
        keyword = self.request.query_params.get('keyword', None)
        location = self.request.query_params.get('location', None)
        org_name = self.request.query_params.get('orgName', None)
        if start_time is not None:
            queryset = queryset.filter(start_time__gte=start_time)
        if end_time is not None:
            queryset = queryset.filter(end_time__lte=end_time)
        if title is not None:
            queryset = queryset.filter(title__contains=title)
        if keyword is not None:
            queryset = queryset.filter(description__contains=keyword)
        if location is not None:
            queryset = queryset.filter(location__contains=location)
        if org_name is not None:
            org_id = Organization.objects.get(name=org_name)
            queryset = queryset.filter(organization_id=org_id)
        return queryset.filter(start_time__gte=timezone.now())

    def list(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            return super().list(req, *args, **kwargs)
        return AuthCheck.unauthorized_response()


class RateEventAPIView(generics.GenericAPIView, AuthCheck):
    """
    Class View to submit ratings for completed events.

    The requesting user must be a volunteer who was signed up for the event, the rating must be between 1 and 5,
    inclusive, the rating must be submitted after the event has ended, and a single volunteer can only rate each event
    once. If the rating was accepted, a 200 status is returned, else a 400 status and an error message is returned.
    """
    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def post(self, req, *args, **kwards):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            volunteer = Volunteer.objects.get(end_user__id=self.get_user_id(req))
            try:
                event = self.get_object()
            except ObjectDoesNotExist:
                return Response(data={"Error": "Event " + str(self.kwargs['event_id']) + " does not exists."}
                                , status=status.HTTP_400_BAD_REQUEST)
            body = json.loads(str(req.body, encoding='utf-8'))
            rating = int(body['rating'])
            if volunteer in event.volunteers.all():
                if 0 < rating < 6:
                    if event.end_time < timezone.now():
                        if Rating.objects.filter(volunteer=volunteer, event__id=event.id).count() == 0:
                            organization = event.organization
                            new_rating = ((organization.rating * organization.raters) + rating) / (
                                        organization.raters + 1)
                            organization.raters += 1
                            organization.rating = round(new_rating, 2)
                            organization.save()

                            Rating.objects.create(event=event, volunteer=volunteer, rating=rating)
                            return Response(data={"Result": "Rating accepted"}, status=status.HTTP_202_ACCEPTED)
                        else:
                            return Response(data={"Error": "This volunteer has already rated this event"},
                                            status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response(data={"Error": "This event has not ended yet, "
                                                       "events can only rated after they have finished."},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(data={"Error": "Rating must be between 1 and 5, inclusive"},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(data={"Error": "Requesting volunteer not registered for this event, "
                                               "volunteers must be signed up for an event to rate it"},
                                status=status.HTTP_400_BAD_REQUEST)
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
                return Response(data={"Success": "Volunteer has been removed from event %s" % self.kwargs['event_id']},
                                status=status.HTTP_202_ACCEPTED)
            else:
                current_event.volunteers.add(vol_id)
                signal_volunteer_signed_up_event.send(Volunteer, vol_id=vol_id, event_id=self.kwargs['event_id'], volunteer=volunteer)
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


# Refactor: 2 classes below should be refactored into a single class
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

                e = OrganizationEventSerializer(instance=event).data
                diffs = []
                for key in body:
                    if key in e:
                        if body[key] != e[key]:
                            diffs.append(key)
                    else:
                        diffs.append(key)

                if len(diffs) > 0:
                    event.start_time = body['start_time']
                    event.end_time = body['end_time']
                    event.date = body['date']
                    event.title = body['title']
                    event.location = body['location']
                    event.description = body['description']
                    event.save(update_fields=diffs)
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


class EventAPIView(generics.RetrieveAPIView):
    """
    Readonly view for a single event
    """
    serializer_class = SearchEventsSerializer

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])


class InviteAPIView(generics.GenericAPIView, AuthCheck):
    """
    View to processes event invites; Returns status 400 if the code is invalid or status 200 and the event_id from the
    invite code
    """

    def get(self, req, *args, **kwargs):
        if AuthCheck.is_authorized(req, settings.SCOPE_TYPES['Volunteer']):
            invite = self.kwargs['invite_code']
            if invite.is_valid():
                event_id = invite.get_data()['event_id']
                return Response(data={"event": event_id}, status=status.HTTP_200_OK)
            return Response(data={"Error": "The provided token is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        return AuthCheck.unauthorized_response()


class InviteVolunteersAPIView(generics.GenericAPIView):
    """
    View to generate an invite code for an event. GET will return an invite code for this event and POST will email
    the provided emails a link to signup for this event
    """

    def get_object(self):
        return Event.objects.get(id=self.kwargs['event_id'])

    def get(self, req, *args, **kwargs):
        """
        Returns the invite code for this invite, expiring in 1 day by default. Method for both Orgs and Volunteers
        """
        try:
            event = self.get_object()
        except ObjectDoesNotExist:
            return Response(data={"Error": "Given event ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        invite_code = self._generate_invite_code(event.id)
        return Response(data={"invite_code": invite_code}, status=status.HTTP_200_OK)

    def _generate_invite_code(self, event_id):
        token = URLToken(data={"event_id": event_id})
        return token.get_token()


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
