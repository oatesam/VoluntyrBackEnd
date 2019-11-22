import json
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from authy.api import AuthyApiClient
from django.test import TestCase
from rest_framework.test import APIRequestFactory, RequestsClient
from rest_framework_simplejwt.views import TokenRefreshView
from .models import Event, Organization, EndUser
from .views import ObtainTokenPairView, VolunteerSignupAPIView, OrganizationSignupAPIView, CheckEmailAPIView, \
    ObtainDualAuthView
from django.conf import settings

authy_api = AuthyApiClient(settings.ACCOUNT_SECURITY_API_KEY)
from .urlTokens.token import URLToken

# TODO: test for double signup of events


class Utilities:

    def volunteer_signup(self, user_dict, expected=201, msg="Volunteer Signup Failed"):
        """
        Test volunteer signup endpoint
        :param user_dict:   Dictionary of volunteer account info.
                            Required keys: email, password, first_name, last_name, birthday
        :param expected:    Expected status code. Default: 201
        :param msg:     Failure message to use for assertEquals. Default: "Volunteer Signup Failed"
        """
        factory = APIRequestFactory()
        signup_data = json.dumps(user_dict)

        signup_view = VolunteerSignupAPIView.as_view()

        signup_request = factory.post(path="api/signup/volunteer/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, expected, msg)

    def volunteer_login(self, user_dict):
        """
        Logs in volunteer from user_dict used in volunteer_signup()
        :param user_dict: user_dict used in volunteer_signup()
        :return: Dictionary with refresh and access tokens
        """
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(user_dict["email"]) + '&password=' + str(user_dict["password"])
        obtain_token_view = ObtainTokenPairView.as_view()

        obtain_token_request = factory.post(path='api/token/', data=obtain_token_data,
                                            content_type='application/x-www-form-urlencoded')
        obtain_token_response = obtain_token_view(obtain_token_request)
        self.assertEqual(obtain_token_response.status_code, 200, "Failed to get token pair for this volunteer.")

        refresh_token = obtain_token_response.data['refresh']
        access_token = obtain_token_response.data['access']

        return {"refresh": refresh_token, "access": access_token}

    def organization_signup(self, user_dict, expected=201, msg="Organization Signup Failed"):
        """
        Test organization signup endpoint
        :param user_dict:   Dictionary of organization account info.
                            Required keys:  email, password, name, street_address, city, sate, phone_number,
                                            organization_motto
        :param expected: Expected status code. Default: 201
        :param msg: Failure message to use for assertEquals. Default: "Organization Signup Failed"
        """
        factory = APIRequestFactory()
        signup_data = json.dumps(user_dict)

        signup_view = OrganizationSignupAPIView.as_view()

        signup_request = factory.post(path="api/signup/organization/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, expected, msg)

    def organization_login(self, user_dict):
        """
        Test organization login endpoint
        :param user_dict:   Dictionary of organization account info.
                            Required keys:  email, password
        :return: Refresh token and access token obtained for this organization
        """
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(user_dict['email']) + '&password=' + str(user_dict['password'])
        obtain_token_view = ObtainTokenPairView.as_view()

        obtain_token_request = factory.post(path='api/token/', data=obtain_token_data,
                                            content_type='application/x-www-form-urlencoded')
        obtain_token_response = obtain_token_view(obtain_token_request)
        self.assertEqual(obtain_token_response.status_code, 200, "Failed to get token pair for this organization.")

        refresh_token = obtain_token_response.data['refresh']
        access_token = obtain_token_response.data['access']
        return {"refresh": refresh_token, "access": access_token}

    def organization_new_event(self, token, event_dict):
        """
        Utility function to post new events
        :param token: Access token for the organization
        :param event_dict: Dictionary of the new event
        """
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + token})
        path = "http://testserver/api/organization/event/"

        response = client.post(path, json=event_dict)
        self.assertEqual(response.status_code, 201, "Utility: Failed to create new event.\n\n" + str(event_dict))

    def volunteer_signup_for_event(self, token, event_id):
        """
        Utility function for volunteers to signup for events
        :param token: Volunteer token
        :param event_id: event id to signup for
        """
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + token})
        path = "http://testserver/api/event/%d/volunteer/" % event_id

        response = client.put(path)
        self.assertEqual(response.status_code, 202, "Utility: Failed to signup volunteer for this event")


class InviteTests(TestCase, Utilities):
    today = datetime.today().day
    month = datetime.today().month
    hour = datetime.today().time().hour
    eventDicts = [
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T' + str(
                hour + 1).zfill(2) + ':00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T' + str(
                hour + 2).zfill(2) + ':00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        },
        {
            'start_time': '2019-' + str(month) + '-' + (
                ("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)) + 'T' + str(
                hour + 1).zfill(2) + ':00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (
                ("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)) + 'T' + str(
                hour + 2).zfill(2) + ':00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        }
    ]

    volunteerDict = {
        "email": "testemail99@gmail.com",
        "password": "testpassword2",
        "first_name": "newuser",
        "last_name": "volunteer",
        "phone_number": "765-426-3669",
        "birthday": "1998-06-12"
    }
    volunteerTokens = {}

    organizationDict = {
        "email": "testorgemail20@gmail.com",
        "password": "testpassword123",
        "name": "Testing Organization",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3669",
        "organization_motto": "The motto"
    }
    organizationTokens = {}

    def setUp(self):
        self.volunteer_signup(self.volunteerDict)
        self.volunteerTokens = self.volunteer_login(self.volunteerDict)
        self.organization_signup(self.organizationDict)
        self.organizationTokens = self.organization_login(self.organizationDict)

        self.organization_new_event(self.organizationTokens['access'], self.eventDicts[0])
        self.organization_new_event(self.organizationTokens['access'], self.eventDicts[1])

    def test_accept_invite(self):
        for i in range(1, len(self.eventDicts) + 1):
            client = RequestsClient()
            client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
            path = "http://testserver/api/event/%d/invite/" % i

            response = client.get(path)
            status = response.status_code
            content = json.loads(response.content)

            self.assertEqual(status, 200, "Response code wasn't 200")
            path = "http://testserver/api/invite/%s/" % content['invite_code']

            response = client.get(path)
            status = response.status_code
            self.assertNotEqual(status, 500, "There was an internal server error.")
            content = json.loads(response.content)

            self.assertEqual(status, 200, "Response code wasn't 200")
            self.assertDictEqual(content, {"event": i})

    def test_bad_invite(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/%d/invite/" % 1

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 200, "Response code wasn't 200")
        path = "http://testserver/api/invite/%s/" % (content['invite_code'][:-2])

        response = client.get(path)
        status = response.status_code
        self.assertNotEqual(status, 500, "There was an internal server error.")
        content = json.loads(response.content)

        self.assertEqual(status, 400, "Invite should be invalid")
        self.assertDictEqual(content, {"Error": "The provided token is invalid."})

    def test_expired_invite(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})

        path = "http://testserver/api/invite/%s/" % URLToken(data={"event_id": 1}, lifetime=timedelta(milliseconds=1)).get_token()

        response = client.get(path)
        status = response.status_code
        self.assertNotEqual(status, 500, "There was an internal server error.")
        content = json.loads(response.content)

        self.assertEqual(status, 400, "Invite should be invalid")
        self.assertDictEqual(content, {"Error": "The provided token is invalid."})

    def test_GET_token(self):
        for i in range(0, len(self.eventDicts)):
            self._test_GET_helper(i + 1)

    def test_GET_bad_event(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/%d/invite/" % 5

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 400, "Event should not exist")
        self.assertDictEqual(content, {"Error": "Given event ID does not exist."})

    def _test_GET_helper(self, event_id):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/%d/invite/" % event_id

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 200, "Response code wasn't 200")
        self.assertEqual(self._get_event_from_URLToken(content['invite_code']), event_id)

    def _get_event_from_URLToken(self, code):
        token = URLToken(token=code)
        data = token.get_data()
        return int(data['event_id'])



class URLTokenTests(TestCase):
    def test_token(self):
        expected_data = {"event_id": 1}
        token = URLToken(data=expected_data)
        self.assertTrue(token.is_valid(), "First token isn't valid")
        self.assertDictEqual(token.get_data(), expected_data, "Actual data didn't match expected data")
        self.assertRegex(token.get_token(), "\S*_\S*")
        token1 = URLToken(token=token.get_token())
        self.assertTrue(token1.is_valid(), "Second token isn't valid")
        self.assertDictEqual(token1.get_data(), expected_data, "Actual data didn't match expected data")

    def test_bad_signature(self):
        expected_data = {"event_id": 1}
        token = URLToken(data=expected_data)
        token1 = URLToken(token=token.get_token()[2:])
        self.assertFalse(token1.is_valid(), "Token should not be valid")
        try:
            token1.get_data()
            self.fail("Should raise exception")
        except Exception:
            pass

    def test_bad_data(self):
        expected_data = {"event_id": 1}
        token = URLToken(data=expected_data)
        token1 = URLToken(token=token.get_token()[:-2])
        self.assertFalse(token1.is_valid(), "Token should not be valid")


class VolunteerOrganizationPageTests(TestCase, Utilities):
    """
    Tests for the Volunteer Organization view
    """
    today = datetime.today().day
    month = datetime.today().month
    hour = datetime.today().time().hour
    eventDicts = [
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T' + str(
                hour + 1).zfill(2) + ':00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T' + str(
                hour + 2).zfill(2) + ':00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        },
        {
            'start_time': '2019-' + str(month) + '-' + (
                ("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)) + 'T' + str(
                hour + 1).zfill(2) + ':00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (
                ("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)) + 'T' + str(
                hour + 2).zfill(2) + ':00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        }
    ]

    volunteerDict = {
        "email": "charlie.frank72@gmail.com",
        "password": "testpassword2",
        "first_name": "newuser",
        "last_name": "volunteer",
        "phone_number": "765-426-3670",
        "birthday": "1998-06-12"
    }
    volunteerTokens = {}

    organizationDict = {
        "email": "testorgemail20@gmail.com",
        "password": "testpassword123",
        "name": "Testing Organization",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3670",
        "organization_motto": "The motto"
    }
    organizationTokens = {}

    def setUp(self):
        self.volunteer_signup(self.volunteerDict)
        self.volunteerTokens = self.volunteer_login(self.volunteerDict)
        self.organization_signup(self.organizationDict)
        self.organizationTokens = self.organization_login(self.organizationDict)

        self.organization_new_event(self.organizationTokens['access'], self.eventDicts[0])
        self.organization_new_event(self.organizationTokens['access'], self.eventDicts[1])

    def test_volunteer_organization(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/organization/%d/" % 1

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 200, "Received unexpected status code")
        self.checkOrgDict(content['organization'])
        self.checkEventsDict(content['events'], self.eventDicts)

    def test_bad_org(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/organization/%d/" % 2

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 400, "Received unexpected status code")
        self.assertDictEqual(content, {"Error": "Organization with the given Id does not exist."})

    def test_view_with_org_token(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens['access']})
        path = "http://testserver/api/organization/%d/" % 2

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 401, "Received unexpected status code")
        self.assertDictEqual(content, {"error": "Invalid token provided. Token lacks required scope."})

    def checkOrgDict(self, actual):
        expected = {
            "end_user": {
                "email": "testorgemail20@gmail.com"
            },
            "name": "Testing Organization",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3670",
            "organization_motto": "The motto"
        }
        self.assertDictEqual(expected, actual, "Organization dictionary didn't match expected")

    def checkEventsDict(self, actual, expected):
        for i in range(0, len(expected)):
            a = actual[i]
            e = expected[i]
            e['id'] = i + 1
            e['organization'] = 1
            self.assertDictEqual(e, a, "Event dict did not match expected")


class OrganizationEventTests(TestCase, Utilities):
    tomorrow = datetime.today() + timedelta(days=1)

    volunteerDicts = [
        {
            "email": "testemail4@gmail.com",
            "password": "testpassword2",
            "first_name": "First user",
            "last_name": "volunteer",
            "phone_number": "765-426-3671",
            "birthday": "1998-06-12"
        },
        {
            "email": "testemail5@gmail.com",
            "password": "testpassword2",
            "first_name": "Second User",
            "last_name": "volunteer",
            "phone_number": "765-426-3672",
            "birthday": "1998-06-12"
        },
        {
            "email": "testemail6@gmail.com",
            "password": "testpassword2",
            "first_name": "Third User",
            "last_name": "volunteer",
            "phone_number": "765-426-3673",
            "birthday": "1998-06-12"
        }
    ]
    volunteerTokens = []

    organizationDict = {
        "email": "testorgemail10@gmail.com",
        "password": "testpassword123",
        "name": "testOrg1",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3674",
        "organization_motto": "The motto"
    }
    organizationTokens = {}

    eventDict = {
        'start_time': str(tomorrow.year) + '-' + str(tomorrow.month) + '-' + str(tomorrow.day) + ' 17:00-05:00',
        'end_time': str(tomorrow.year) + '-' + str(tomorrow.month) + '-' + str(tomorrow.day) + ' 18:00-05:00',
        'date': str(tomorrow.year) + '-' + str(tomorrow.month) + '-' + str(tomorrow.day),
        'title': 'Let\'s test',
        'location': 'IU',
        'description': 'Test event'
    }
    eventId = None

    def setUp(self):
        for volunteer in self.volunteerDicts:
            self.volunteer_signup(volunteer)
            self.volunteerTokens.append(self.volunteer_login(volunteer))
        self.organization_signup(self.organizationDict)
        self.organizationTokens = self.organization_login(self.organizationDict)
        self.eventId = self.new_event(self.eventDict)

    def new_event(self, event_dict):
        event_dict['organization'] = Organization.objects.get(id=1)
        event = Event.objects.create(**event_dict)
        return event.id

    def test_volunteers(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens['access']})
        path = "http://testserver/api/event/%d/volunteers/" % 1

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 200)
        self.assertEqual(content['number'], 0)
        self.assertEqual(len(content['volunteers']), 0)

        self.volunteer_signup_for_event(self.volunteerTokens[0]['access'], self.eventId)
        self.volunteer_signup_for_event(self.volunteerTokens[1]['access'], self.eventId)

        response = client.get(path)
        status = response.status_code
        content = json.loads(response.content)

        self.assertEqual(status, 200)
        self.assertEqual(content['number'], 2)
        self.assertEqual(content['volunteers'], [{'name': self.volunteerDicts[0]['first_name'] + " " + self.volunteerDicts[0]['last_name']}, {'name': self.volunteerDicts[1]['first_name'] + " " + self.volunteerDicts[1]['last_name']}])


class EventEmailTests(TestCase, Utilities):
    today = datetime.today().day
    month = datetime.today().month
    hour = datetime.today().time().hour
    eventDicts = [
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T'
                          + str(hour + 1).zfill(2) + ':00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T'
                        + str(hour + 2).zfill(2) + ':00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        },
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)) + 'T' + str(
                hour + 1).zfill(2) + ':00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)) + 'T' + str(
                hour + 2).zfill(2) + ':00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today + 1)) if today + 1 < 10 else str(today + 1)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        }
    ]

    volunteerDict = {
        "email": "charlie.frank72@gmail.com",
        "password": "testpassword2",
        "first_name": "newuser",
        "last_name": "volunteer",
        "phone_number": "765-426-3675",
        "birthday": "1998-06-12"
    }
    volunteerTokens = {}

    organizationDict_real = {
        "email": "testorgemail10@gmail.com",
        "password": "testpassword123",
        "name": "Testing Organization",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3676",
        "organization_motto": "The motto"
    }
    organizationTokens_real = {}

    organizationDict_fake = {
        "email": "testorgemail20@gmail.com",
        "password": "testpassword123",
        "name": "Fake Testing Organization",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3677",
        "organization_motto": "The motto"
    }
    organizationTokens_fake = {}

    def setUp(self):
        self.volunteer_signup(self.volunteerDict)
        self.volunteerTokens = self.volunteer_login(self.volunteerDict)
        self.organization_signup(self.organizationDict_real)
        self.organizationTokens_real = self.organization_login(self.organizationDict_real)

        self.organization_signup(self.organizationDict_fake)
        self.organizationTokens_fake = self.organization_login(self.organizationDict_fake)

        self.organization_new_event(self.organizationTokens_real['access'], self.eventDicts[0])
        self.organization_new_event(self.organizationTokens_real['access'], self.eventDicts[1])
        self.volunteer_signup_for_event(self.volunteerTokens['access'], 1)

    def test_emails(self):
        # FIXME: assert email message
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens_real['access']})
        path = "http://testserver/api/event/%d/email/" % 1

        email_dict = {
            'message': 'This is a test email from EventEmailTests.test_emails',
            'subject': 'Test case email',
            'replyto': 'testcase@gmail.com'
        }

        response = client.post(path, json=email_dict)
        self.assertEqual(response.status_code, 200)

    def test_no_volunteers(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens_real['access']})
        path = "http://testserver/api/event/%d/email/" % 2

        email_dict = {
            'message': 'This is a test email from EventEmailTests.test_emails',
            'subject': 'Test case email',
            'replyto': 'testcase@gmail.com'
        }

        response = client.post(path, json=email_dict)
        self.assertEqual(response.status_code, 200)

    def test_bad_event(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens_real['access']})
        path = "http://testserver/api/event/%d/email/" % 3

        email_dict = {
            'message': 'This is a test email from EventEmailTests.test_emails',
            'subject': 'Test case email',
            'replyto': 'testcase@gmail.com'
        }

        response = client.post(path, json=email_dict)
        self.assertEqual(response.status_code, 400,
                         "Email was sent for an event which shouldn't exist." if response.status_code == 200
                         else "Unexpected response code")
        self.assertDictEqual(json.loads(response.content),
                             {"Error": "Given event ID does not exist."},
                             "Email was sent for an event which shouldn't exist." if response.status_code == 200
                             else "Unexpected response for non existent event id")

    def test_bad_organization(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens_fake['access']})
        path = "http://testserver/api/event/%d/email/" % 1

        email_dict = {
            'message': 'This is a test email from EventEmailTests.test_emails',
            'subject': 'Test case email',
            'replyto': 'testcase@gmail.com'
        }

        response = client.post(path, json=email_dict)
        self.assertEqual(response.status_code, 401,
                         "Wrong organization was able to send an email" if response.status_code == 200
                         else "Unexpected response code")
        self.assertDictEqual(json.loads(response.content),
                             {"Unauthorized": "Requesting token does not manage this event."},
                             "Unexpected response for unauthorized organization")


class OrganizationCreateEvent(TestCase, Utilities):
    """
    Test the endpoint to create event
    """

    def test_create_event(self):
        organization_dict = {
            "email": "testorgemail5@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3677",
            "organization_motto": "The motto"
        }
        Utilities.organization_signup(self, organization_dict)
        tokens = Utilities.organization_login(self, organization_dict)
        self.create_event(tokens['access'])

    def create_event(self, access_token, expected=201):
        newEvent = {
            "start_time": "2019-10-19 12:00:00-05:00",
            "end_time": "2019-10-20 13:00:00-05:00",
            "date": "2019-10-19",
            "title": "testActivity",
            "location": "SICE",
            "description": "testing endpoint"
        }

        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/organization/event/"

        create_event_response = client.post(path, json=newEvent)
        self.assertEqual(create_event_response.status_code, expected, msg=create_event_response.content)


class OrganizationEditEvent(TestCase, Utilities):
    """
    Test the endpoint to edit event
    """
    def test_create_event(self):
        organization_dict = {
            "email": "testmail@gmail.com",
            "password": "testpassword123",
            "name": "testOrg",
            "street_address": "700 N, Woodlawn Lane",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3678",
            "organization_motto": "Org Motto"
        }
        Utilities.organization_signup(self, organization_dict)
        tokens = Utilities.organization_login(self, organization_dict)
        self.create_event(tokens['access'])

    def create_event(self, access_token, expected=201):
        newEvent = {
            "id": 1,
            "start_time": "2019-10-25 12:00:00-05:00",
            "end_time": "2019-10-25 13:00:00-05:00",
            "date": "2019-10-25",
            "title": "testevent",
            "location": "testlocation",
            "description": "testing endpoint"
        }

        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/organization/event/"

        create_event_response = client.post(path, json=newEvent)
        self.assertEqual(create_event_response.status_code, expected, msg="Failed to create event")
        self.edit_event(access_token, newEvent)

    def edit_event(self, access_token, newEvent):
        editDetails = {
            "description": "testdescription"
        }
        newEvent.update(editDetails)
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/organization/updateEvent/"
        create_event_response = client.put(path, json=newEvent)
        self.assertEqual(create_event_response.status_code, 201, msg="Failed to edit event")
        path = "http://testserver/api/organization/event/1/"
        create_event_response = client.get(path)
        self.assertEqual(create_event_response.status_code, 200, msg="Failed to get edited event")


class EventSearchTest(TestCase, Utilities):

    today = datetime.today().day
    month = datetime.today().month

    events = [
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T17:00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)) + 'T18:00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today)) if today < 10 else str(today)),
            'title': 'First event',
            'location': 'IU',
            'description': 'Test event'
        },
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today + 2)) if today + 2 < 10 else str(today + 2)) + 'T17:00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today + 2)) if today + 2 < 10 else str(today + 2)) + 'T18:00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today + 2)) if today + 2 < 10 else str(today + 2)),
            'title': 'Second event',
            'location': 'IU',
            'description': 'Test event'
        },
        {
            'start_time': '2019-' + str(month) + '-' + (("0" + str(today + 3)) if today + 3 < 10 else str(today + 3)) + 'T17:00:00-05:00',
            'end_time': '2019-' + str(month) + '-' + (("0" + str(today + 3)) if today + 3 < 10 else str(today + 3)) + 'T18:00:00-05:00',
            'date': '2019-' + str(month) + '-' + (("0" + str(today + 3)) if today + 3 < 10 else str(today + 3)),
            'title': 'Third event',
            'location': 'IU',
            'description': 'Test event'
        },
    ]

    volunteerDict = {
        "email": "testemail2@gmail.com",
        "password": "testpassword2",
        "first_name": "newuser",
        "last_name": "volunteer",
        "phone_number": "765-426-3679",
        "birthday": "1998-06-12"
    }
    volunteerTokens = {}

    organizationDict = {
        "email": "testorgemail10@gmail.com",
        "password": "testpassword123",
        "name": "testOrg1",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3680",
        "organization_motto": "The motto"
    }
    organizationTokens = {}

    time = datetime.time(datetime.today())
    if time >= datetime.strptime('17:00:00-0500', '%H:%M:%S%z').time():
        expected_count = 2
    else:
        expected_count = 3

    def setUp(self):
        self.volunteer_signup(self.volunteerDict)
        self.volunteerTokens = self.volunteer_login(self.volunteerDict)
        self.organization_signup(self.organizationDict)
        self.organizationTokens = self.organization_login(self.organizationDict)
        self.expectedEventIds = self.make_events(self.events)

    def test_event_search_with_title(self):
        client= RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/events/?title=Second event"
        data_response = client.get(path)
        content = json.loads(data_response.content)
        self.assertEqual(len(content), 1, "Search result didn't match")

    def test_event_search_with_keyword(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/events/?keyword=event"
        data_response = client.get(path)
        content = json.loads(data_response.content)
        self.assertEqual(len(content), self.expected_count, "Search result didn't match")

    def test_event_search_with_location(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/events/?location=IU"
        data_response = client.get(path)
        content = json.loads(data_response.content)
        self.assertEqual(len(content), self.expected_count, "Search result didn't match")

    def test_event_search_with_date_range(self):
        start_time = '2019-' + str(self.month) + '-' + (("0" + str(self.today)) if self.today < 10 else str(self.today)) + 'T10:00:00-05:00'
        end_time = '2019-' + str(self.month) + '-' + (("0" + str(self.today + 3)) if self.today + 4 < 10 else str(self.today + 4)) + 'T18:00:00-05:00'
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/events/?start_time="+str(start_time)+"&end_time="+str(end_time)
        data_response = client.get(path)
        content = json.loads(data_response.content)
        self.assertEqual(len(content), self.expected_count, "Search result didn't match")

    def test_event_search_with_orgName(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/events/?orgName=testOrg1"
        data_response = client.get(path)
        content = json.loads(data_response.content)
        self.assertEqual(len(content), self.expected_count, "Search result didn't match")

    def test_event_search(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/events/"
        data_response = client.get(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 200, "Search status was not 200")

        time = datetime.time(datetime.today())
        if time >= datetime.strptime('17:00:00-0500', '%H:%M:%S%z').time():
            slice_start = 1
        else:
            slice_start = 0

        expected_dicts = self.make_assert_dicts(self.events[slice_start:3], self.expectedEventIds[slice_start:3], self.organizationDict['name'])
        self.assertEqual(len(content), len(expected_dicts),
                         "API failed to return expected number of events. Returned %d events but expected %d."
                         % (len(content), len(expected_dicts)))
        for i in range(0, len(content)):
            self.assertDictEqual(content[i], expected_dicts[i], "A returned JSON didn't match the expected dict.")
            self.get_single_event(content[i]['id'], content[i])

    def get_single_event(self, event_id, expected):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/volunteer/event/"

        data_response = client.get(path + str(event_id) + "/")
        content = json.loads(data_response.content)
        status = data_response.status_code
        self.assertEqual(status, 200, "Single event status wasn't 200. Got this instead: " + str(status))
        self.assertDictEqual(content, expected, "Actual dict didn't match the expected dict.")

    def make_assert_dicts(self, expected_events, expected_ids, organization_name):
        self.assertEqual(len(expected_events), len(expected_ids),
                         "Length of event dictionary list needs to equal length of expected id list. "
                         "\nLength of expected id: %d\nLength of expected events: %d" % (len(expected_ids),
                                                                                         len(expected_events)))
        for i in range(0, len(expected_events)):
            current_id = expected_ids[i]
            current_dict = expected_events[i]
            current_dict['organization'] = {"id": 1, "name": organization_name}
            current_dict['id'] = current_id
        return expected_events

    def make_events(self, events):
        event_ids = []
        for e in events:
            event_ids.append(self.new_event(e))
        return event_ids

    def new_event(self, event_dict):
        event_dict['organization'] = Organization.objects.get(id=1)
        event = Event.objects.create(**event_dict)
        return event.id


class VolunteerEventSignupTest(TestCase, Utilities):
    tomorrow = datetime.today() + timedelta(days=1)

    volunteerDict = {
        "email": "testemail2@gmail.com",
        "password": "testpassword2",
        "first_name": "newuser",
        "last_name": "volunteer",
        "phone_number": "765-426-3681",
        "birthday": "1998-06-12"
    }
    volunteerTokens = {}

    organizationDict = {
        "email": "testorgemail10@gmail.com",
        "password": "testpassword123",
        "name": "testOrg1",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-3682",
        "organization_motto": "The motto"
    }
    organizationTokens = {}

    eventDict = {
        'start_time': str(tomorrow.year) + '-' + str(tomorrow.month) + '-' + str(tomorrow.day) + ' 17:00-05:00',
        'end_time': str(tomorrow.year) + '-' + str(tomorrow.month) + '-' + str(tomorrow.day) + ' 18:00-05:00',
        'date': str(tomorrow.year) + '-' + str(tomorrow.month) + '-' + str(tomorrow.day),
        'title': 'Let\'s test',
        'location': 'IU',
        'description': 'Test event'
    }
    eventId = None

    def setUp(self):
        self.volunteer_signup(self.volunteerDict)
        self.volunteerTokens = self.volunteer_login(self.volunteerDict)
        self.organization_signup(self.organizationDict)
        self.organizationTokens = self.organization_login(self.organizationDict)
        self.eventId = self.new_event(self.eventDict)

    def test_volunteer_event_signup(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/%d/volunteer/" % self.eventId

        data_response = client.put(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 202, msg="Volunteer event signup failed.")
        self.assertDictEqual(content, {"Success": "Volunteer has signed up for event %d" % self.eventId})
        self.confirm_signup(self.eventId)

        data_response = client.put(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 202, msg="Volunteer event unsignup failed.")
        self.assertDictEqual(content, {"Success": "Volunteer has been removed from event %d" % self.eventId})

    def test_check_event_signup(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/%d/check/" % self.eventId

        data_response = client.get(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 200, msg="Signup check failed.")
        self.assertDictEqual(content, {"Signed-up": "false"}, msg="Volunteer shouldn't be signed up.")

        self.volunteer_signup_for_event(self.volunteerTokens['access'], self.eventId)
        data_response = client.get(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 200, msg="Signup check failed.")
        self.assertDictEqual(content, {"Signed-up": "true"}, msg="Volunteer should be signed up.")

    def test_check_bad_event_signup(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/%d/check/" % (self.eventId + 1)

        data_response = client.get(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 400)
        self.assertDictEqual(content, {"Error": "Given event ID does not exist."})


    def test_volunteer_event_signup_organizer_token(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens['access']})
        path = "http://testserver/api/event/%d/volunteer/" % self.eventId

        data_response = client.put(path)
        # content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 401, msg="Organization was able to sig nup for an event")

    def test_volunteer_event_signup_bad_event_id(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/event/2/volunteer/"

        data_response = client.put(path)
        content = json.loads(data_response.content)
        status = data_response.status_code

        self.assertEqual(status, 400)
        self.assertDictEqual(content, {"Error": "Given event ID does not exist."})

    def confirm_signup(self, event_id):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.volunteerTokens['access']})
        path = "http://testserver/api/volunteer/events/"

        data_response = client.get(path)
        content = json.loads(data_response.content)

        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], event_id)

    def new_event(self, event_dict):
        event_dict['organization'] = Organization.objects.get(id=1)
        event = Event.objects.create(**event_dict)
        return event.id


class OrganizationDashboardTest(TestCase):

    def test_organization_account_info(self):
        """
        Validate the organization information passed from endpoint

        """
        organizationDict = {
            "email": "testorgemail10@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3683",
            "organization_motto": "The motto"
        }
        SignupLoginTest.Test_organization_signup(self, organizationDict)
        refresh_token, access_token = SignupLoginTest.Test_organization_login(self, organizationDict)
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/organization/"

        volunteer_data_response = client.get(path)
        content = json.loads(volunteer_data_response.content)
        self.assertEqual(organizationDict['name'], content['name'])


class VolunteerDashboardTest(TestCase):
    """
    Non existing email
    """
    newUserDict = {"email": "testemail2@gmail.com",
                   "password": "testpassword2",
                   "first_name": "newuser",
                   "last_name": "volunteer",
                    "phone_number": "765-426-3684",
                   "birthday": "1998-06-12"}

    def test_volunteer_account_info(self):
        """
        This method validates the login credentials of the volunteer
        """
        self.Test_volunteer_signup(self.newUserDict)
        refresh_token, access_token = self.Test_volunteer_login(self.newUserDict)
        self.Test_volunteer_account(self.newUserDict, access_token)

    def Test_volunteer_signup(self, newUserDict, expected=201, msg="Volunteer Signup Failed"):
        """
        Test volunteer signup endpoint
        :param newUserDict:   Dictionary of volunteer account info.
                            Required keys: email, password, first_name, last_name, phone_number, birthday
        :param expected:    Expected status code. Default: 201
        :param msg:     Failure message to use for assertEquals. Default: "Volunteer Signup Failed"
        """
        factory = APIRequestFactory()
        signup_data = json.dumps(newUserDict)

        signup_view = VolunteerSignupAPIView.as_view()

        signup_request = factory.post(path="api/signup/volunteer/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, expected, msg)

    def Test_volunteer_login(self, userdict):
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(userdict["email"]) + '&password=' + str(userdict["password"])
        obtain_token_view = ObtainTokenPairView.as_view()

        obtain_token_request = factory.post(path='api/token/', data=obtain_token_data,
                                            content_type='application/x-www-form-urlencoded')
        obtain_token_response = obtain_token_view(obtain_token_request)
        self.assertEqual(obtain_token_response.status_code, 200, "Failed to get token pair for this volunteer.")

        refresh_token = obtain_token_response.data['refresh']
        access_token = obtain_token_response.data['access']

        return refresh_token, access_token

    def Test_volunteer_account(self, userdict, access_token, expected_end_user=1):
        """
        Test volunteer information endpoint
        :param userdict: Dictionary used to create user.
            Needs to have the following keys: first_name, last_name, birthday
        :param access_token: Access token for this user
        :param expected_end_user: Expected end_user id
        """
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/volunteer/"

        volunteer_data_response = client.get(path)
        content = json.loads(volunteer_data_response.content)

        # Remove email and password keys and add end_user key for assert
        userdict['end_user'] = expected_end_user
        userdict.pop('email', None)
        userdict.pop('password', None)

        self.assertDictEqual(userdict, content)


class DualAuthTest(TestCase, Utilities):
    """
    Test Dual Authentication
    """

    newUserDict = {"email": "testemail2@gmail.com",
                   "password": "testpassword2",
                   "first_name": "newuser",
                   "last_name": "volunteer",
                   "phone_number": "765-426-3685",
                   "birthday": "1998-06-12"}

    def test_authy_user(self):
        self.Test_authy_volunteer_signup(self.newUserDict)
        refresh_token, access_token = self.Test_authy_volunteer_login(self.newUserDict)
        self.Test_authy_volunteer_account(self.newUserDict, access_token)
        self.Test_bad_authy_login(access_token)


    def Test_authy_volunteer_signup(self, newUserDict, expected=201, msg="Authy ID Creation Failed"):
        """
        Test volunteer signup endpoint for creation of authy_id
        :param newUserDict:   Dictionary of volunteer account info.
                            Required keys: email, password, first_name, last_name, phone_number, birthday
        :param expected:    Expected status code. Default: 201
        :param msg:     Failure message to use for assertEquals. Default: "Volunteer Signup Failed"
        """
        factory = APIRequestFactory()
        signup_data = json.dumps(newUserDict)

        signup_view = VolunteerSignupAPIView.as_view()

        signup_request = factory.post(path="api/signup/volunteer/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, expected, msg)

    def Test_authy_volunteer_login(self, userdict):
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(userdict["email"]) + '&password=' + str(userdict["password"])
        obtain_token_view = ObtainTokenPairView.as_view()

        obtain_token_request = factory.post(path='api/token/', data=obtain_token_data,
                                            content_type='application/x-www-form-urlencoded')
        obtain_token_response = obtain_token_view(obtain_token_request)
        self.assertEqual(obtain_token_response.status_code, 200, "Failed to get token pair for this volunteer.")

        refresh_token = obtain_token_response.data['refresh']
        access_token = obtain_token_response.data['access']

        return refresh_token, access_token

    def Test_bad_authy_login(self, access_token):
        obtain_token_data = {"token": "10000"}
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/token/dualauth/"
        response = client.get(path)
        status = response.status_code

        self.assertEqual(status, 405, "This should return a 405.")


    def Test_authy_volunteer_account(self, userdict, access_token, expected_end_user=1):
        """
        Test volunteer information endpoint
        :param userdict: Dictionary used to create user.
            Needs to have the following keys: first_name, last_name, birthday
        :param access_token: Access token for this user
        :param expected_end_user: Expected end_user id
        """
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + access_token})
        path = "http://testserver/api/volunteer/"

        volunteer_data_response = client.get(path)
        content = json.loads(volunteer_data_response.content)
        end_user = EndUser.objects.get(id=content['end_user'])
        exp_end_user = EndUser.objects.get(id=expected_end_user)
        self.assertEqual(end_user.authy_id, exp_end_user.authy_id)


class SignupLoginTest(TestCase):
    def test_checkemail(self):
        """
        Test emailcheck endpoint
        """
        email = "email123@gmail.com"
        password = "testpassword123"

        self.Test_emailcheck("shouldntexist@gmail.com", 204, "This email shouldn't exist.")
        self.Test_volunteer_signup(email, password)
        self.Test_emailcheck(email, 202, "This email should exist.")

    def test_volunteer_duplicate_signup(self):
        """
        Test if email can be used to signup for two volunteer accounts
        """
        email = "volunteertestemail1@gmail.com"
        password = "testpassword123"

        self.Test_volunteer_signup(email, password)
        self.Test_volunteer_signup(email, password, 409, "Email already has an account, shouldn't be able to signup")

    def test_organization_duplicate_signup(self):
        """
        Test if email can be used to signup for two organization accounts
        """
        organization_dict = {
            "email": "testorgemail10@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3686",
            "organization_motto": "The motto"
        }

        self.Test_organization_signup(organization_dict)
        self.Test_organization_signup(organization_dict, 409, "Email already has an account, shouldn't be able to signup")

    def test_organization_volunteer_duplicate_signup(self):
        """
        Test if email can be used to signup for organization account then volunteer account.
        """
        organization_dict = {
            "email": "testorgemail10@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3687",
            "organization_motto": "The motto"
        }

        self.Test_organization_signup(organization_dict)
        self.Test_volunteer_signup(organization_dict['email'], organization_dict['password'], 409, "Email has an organization account, shouldn't be able to "
                                                         "signup for volunteer account")

    def test_volunteer_organization_duplicate_signup(self):
        """
        Test if email can be used to signup for volunteer account then organization account.
        """
        organization_dict = {
            "email": "testorgemail10@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3688",
            "organization_motto": "The motto"
        }

        self.Test_volunteer_signup(organization_dict['email'], organization_dict['password'])
        self.Test_organization_signup(organization_dict, 409, "Email has an organization account, shouldn't be able to "
                                                            "signup for volunteer account")

    def test_volunteer_signup_login(self):
        """
        Test volunteer signup and login endpoints and test volunteer access and refresh tokens
        """
        email = "volunteertestemail@gmail.com"
        password = "testpassword123"

        self.Test_volunteer_signup(email, password)
        refresh_token, access_token = self.Test_volunteer_login(email, password)
        self.Test_volunteer_access_token(access_token)
        self.Test_refresh_token(refresh_token)

    def test_organization(self):
        """
        Test organization signup and login endpoints and test organization access and refresh tokens
        """
        organization_dict = {
            "email": "testorgemail10@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "street_address": "1 IU st",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3689",
            "organization_motto": "The motto"
        }

        self.Test_organization_signup(organization_dict)
        refresh_token, access_token = self.Test_organization_login(organization_dict)
        self.Test_organization_access_token(access_token)
        self.Test_refresh_token(refresh_token)

    def test_bad_organization(self):
        """
        Test organization signup with missing information.
        """
        organization_dict = {
            "email": "testorgemail10@gmail.com",
            "password": "testpassword123",
            "name": "testOrg1",
            "city": "Bloomington",
            "state": "Indiana",
            "phone_number": "765-426-3690",
            "organization_motto": "The motto"
        }

        self.Test_organization_signup(organization_dict, expected=400,
                                      msg="Organization should not be able to signup without all required fields")

    def Test_volunteer_signup(self, email, password, expected=201, msg="Volunteer Signup Failed"):
        """
        Test volunteer signup endpoint
        :param email
        :param password
        :param expected: Expected status code. Default: 201
        :param msg: Failure message to use for assertEquals. Default: "Volunteer Signup Failed"
        """
        factory = APIRequestFactory()
        signup_data = json.dumps({"email": email, "password": password, "first_name": "test",
                                  "last_name": "volunteer", "phone_number": "765-426-3691", "birthday": "1998-06-12"})

        signup_view = VolunteerSignupAPIView.as_view()

        signup_request = factory.post(path="api/signup/volunteer/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, expected, msg)

    def Test_volunteer_login(self, email, password):
        """
        Test volunteer login endpoint
        :param email: Email used in Test_volunteer_signup
        :param password: Password used in Test_volunteer_signup
        :return: Refresh token and access token obtained for this volunteer
        """
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(email) + '&password=' + str(password)
        obtain_token_view = ObtainTokenPairView.as_view()

        obtain_token_request = factory.post(path='api/token/', data=obtain_token_data,
                                            content_type='application/x-www-form-urlencoded')
        obtain_token_response = obtain_token_view(obtain_token_request)
        self.assertEqual(obtain_token_response.status_code, 200, "Failed to get token pair for this volunteer.")

        refresh_token = obtain_token_response.data['refresh']
        access_token = obtain_token_response.data['access']
        return refresh_token, access_token

    def Test_volunteer_access_token(self, token):
        # TODO: Test volunteer access token when endpoints are available
        pass

    def Test_organization_signup(self, user_dict, expected=201, msg="Organization Signup Failed"):
        """
        Test organization signup endpoint
        :param user_dict:   Dictionary of organization account info.
                            Required keys:  email, password, name, street_address, city, sate, phone_number,
                                            organization_motto
        :param expected: Expected status code. Default: 201
        :param msg: Failure message to use for assertEquals. Default: "Organization Signup Failed"
        """
        factory = APIRequestFactory()
        signup_data = json.dumps(user_dict)

        signup_view = OrganizationSignupAPIView.as_view()

        signup_request = factory.post(path="api/signup/organization/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, expected, msg)

    def Test_organization_login(self, user_dict):
        """
        Test organization login endpoint
        :param user_dict:   Dictionary of organization account info.
                            Required keys:  email, password
        :return: Refresh token and access token obtained for this organization
        """
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(user_dict['email']) + '&password=' + str(user_dict['password'])
        obtain_token_view = ObtainTokenPairView.as_view()

        obtain_token_request = factory.post(path='api/token/', data=obtain_token_data,
                                            content_type='application/x-www-form-urlencoded')
        obtain_token_response = obtain_token_view(obtain_token_request)
        self.assertEqual(obtain_token_response.status_code, 200, "Failed to get token pair for this organization.")

        refresh_token = obtain_token_response.data['refresh']
        access_token = obtain_token_response.data['access']
        return refresh_token, access_token

    def Test_organization_access_token(self, token):
        # TODO: Test organization access token when endpoints are available
        pass

    def Test_refresh_token(self, token):
        """
        Test refresh token
        :param token: Refresh Token
        :return: New access token
        """
        factory = APIRequestFactory()
        refresh_token_data = 'refresh=' + token
        refresh_token_view = TokenRefreshView.as_view()

        refresh_token_request = factory.post(path="api/refresh/", data=refresh_token_data,
                                             content_type='application/x-www-form-urlencoded')
        refresh_token_response = refresh_token_view(refresh_token_request)
        self.assertEqual(refresh_token_response.status_code, 200, "Failed to refresh token.")

        access_token = refresh_token_response.data['access']
        return access_token

    def Test_emailcheck(self, email, expected, msg=None):
        """
        Tests api/checkemail/
        :param email: Email to test with
        :param expected: Expected status code for Email
        :param msg: Failure message to use for assertEquals
        """
        factory = APIRequestFactory()
        email_data = json.dumps({"email": email})
        email_view = CheckEmailAPIView.as_view()

        email_request = factory.post(path="api/checkemail/", data=email_data, content_type="json")
        email_response = email_view(email_request)

        self.assertEqual(email_response.status_code, expected, msg)


