import json

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ObtainTokenPairView, VolunteerAPIView, OrganizationAPIView


class SignupLoginTest(TestCase):
    def test_volunteer(self):
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
        Test organization signup and login endpoints and test volunteer access and refresh tokens
        """
        email = "organizationtestemail@gmail.com"
        password = "testpassword123"

        self.Test_organization_signup(email, password)
        refresh_token, access_token = self.Test_organization_login(email, password)
        self.Test_organization_access_token(access_token)
        self.Test_refresh_token(refresh_token)

    def Test_volunteer_signup(self, email, password):
        """
        Test volunteer signup endpoint
        :param email
        :param password
        """
        factory = APIRequestFactory()
        signup_data = json.dumps({"email": email, "password": password, "first_name": "test",
                                 "last_name": "volunteer", "birthday": "1998-06-12"})

        signup_view = VolunteerAPIView.as_view()

        signup_request = factory.post(path="api/signup/volunteer/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, 201, "Volunteer Signup Failed")

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

    def Test_organization_signup(self, email, password):
        """
        Test volunteer signup endpoint
        :param email
        :param password
        """
        factory = APIRequestFactory()
        signup_data = json.dumps({"email": email, "password": password, "name": "TestOrg"})

        signup_view = OrganizationAPIView.as_view()

        signup_request = factory.post(path="api/signup/organization/", data=signup_data, content_type="json")
        signup_response = signup_view(signup_request)
        self.assertEqual(signup_response.status_code, 201, "Organization Signup Failed")

    def Test_organization_login(self, email, password):
        """
        Test organization login endpoint
        :param email: Email used in Test_organization_signup
        :param password: Password used in Test_organization_signup
        :return: Refresh token and access token obtained for this organization
        """
        factory = APIRequestFactory()
        obtain_token_data = 'email=' + str(email) + '&password=' + str(password)
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
