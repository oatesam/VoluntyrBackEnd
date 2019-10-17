import json

from django.test import TestCase
from rest_framework.test import APIRequestFactory, RequestsClient
from rest_framework_simplejwt.views import TokenRefreshView

from .models import Event, Organization
from .views import ObtainTokenPairView, VolunteerSignupAPIView, OrganizationSignupAPIView, CheckEmailAPIView


# TODO: Refactor Tests.py to be more simple and modular


class VolunteerEventSignupTest(TestCase):
    volunteerDict = {
        "email": "testemail2@gmail.com",
        "password": "testpassword2",
        "first_name": "newuser",
        "last_name": "volunteer",
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
        "phone_number": "1-800-000-0000",
        "organization_motto": "The motto"
    }
    organizationTokens = {}

    eventDict = {
        'start_time': '2019-10-19 17:00-05:00',
        'end_time': '2019-10-19 18:00-05:00',
        'date': '2019-10-19',
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

    def test_volunteer_event_signup_bad_token(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organizationTokens['access']})
        path = "http://testserver/api/event/%d/volunteer/" % self.eventId

        data_response = client.put(path)
        content = json.loads(data_response.content)
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
        # event.save()
        return event.id

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


class VolunteerDashboardTest(TestCase):
    """
    Non existing email
    """
    newUserDict = {"email": "testemail2@gmail.com",
                   "password": "testpassword2",
                   "first_name": "newuser",
                   "last_name": "volunteer",
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
                            Required keys: email, password, first_name, last_name, birthday
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

    def Test_volunteer_account(self, userdict,  access_token, expected_end_user=1):
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
            "phone_number": "1-800-000-0000",
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
            "phone_number": "1-800-000-0000",
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
            "phone_number": "1-800-000-0000",
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
            "phone_number": "1-800-000-0000",
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
            "phone_number": "1-800-000-0000",
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
                                  "last_name": "volunteer", "birthday": "1998-06-12"})

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
