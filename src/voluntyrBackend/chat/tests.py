import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import RequestsClient

from api import tests
from api.models import EndUser

from chat.models import Room, Membership


class Utilities(tests.Utilities):
    def to_dict(self, response):
        return json.loads(str(response.content, encoding='utf-8'))

    def to_json(self, d):
        return json.dumps(d)

    def get_chat_rooms(self, token):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + token})
        path = "http://testserver/chat/rooms/"

        response = client.get(path)
        status = response.status_code
        self.assertEqual(status, 201, "Utility: Get Chat Rooms")
        content = self.to_dict(response)
        return content['rooms']


# https://channels.readthedocs.io/en/latest/tutorial/part_4.html
class CreateChatRoomTest(TestCase, Utilities):
    organization_dict = {
        "email": "testorgemail5@gmail.com",
        "password": "testpassword123",
        "name": "testOrg1",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-6891",
        "organization_motto": "The motto"
    }
    organization_tokens = {}

    event_dict = {
        'start_time': timezone.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        'end_time': (timezone.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S%z"),
        'date': timezone.now().strftime("%Y-%m-%d"),
        "title": "testActivity",
        "location": "SICE",
        "description": "testing endpoint"
    }

    def setUp(self):
        self.organization_signup(self.organization_dict)
        self.organization_tokens = self.organization_login(self.organization_dict)

    def test_create_event_chat(self):
        rooms_before_new_event = Room.objects.all().count()
        self.organization_new_event(self.organization_tokens['access'], self.event_dict)
        rooms_after_new_event = Room.objects.all().count()

        self.assertEqual(rooms_after_new_event, rooms_before_new_event + 1, "Chat room creation failed")

        room = self.get_chat_rooms(self.organization_tokens['access'])[0]
        self.assertEqual(1, room)


class GetRoomsTest(TestCase, Utilities):
    organization_dict = {
        "email": "testorgemail111@gmail.com",
        "password": "testpassword123",
        "name": "testOrg1",
        "street_address": "1 IU st",
        "city": "Bloomington",
        "state": "Indiana",
        "phone_number": "765-426-6891",
        "organization_motto": "The motto"
    }
    organization_tokens = {}

    def setup(self):
        self.organization_signup(self.organization_dict)
        self.organization_tokens = self.organization_login(self.organization_dict)

        end_user = EndUser.objects.get(id=1)

        self.room1 = Room.objects.create(title="TestRoom 1")
        Membership.objects.create(end_user=end_user, room=self.room1)

        self.room2 = Room.objects.create(title="TestRoom 2")
        Membership.objects.create(end_user=end_user, room=self.room2)

        self.room3 = Room.objects.create(title="TestRoom 3")

    def test_get_rooms(self):
        self.failIf(self.organization_tokens is None or self.organization_tokens.keys() != ['access', 'refresh'], msg="Org Tokens Dict: " + str(self.organization_tokens))
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organization_tokens["access"]})
        path = "http://testserver/chat/rooms/"

        response = client.get(path)
        status = response.status_code
        self.assertEqual(status, 201, "Utility: Get Chat Rooms")
        content = self.to_dict(response)

        expected = {
            "rooms": [
                {
                    "title": "TestRoom 1",
                    "id": self.room1.id
                },
                {
                    "title": "TestRoom 2",
                    "id": self.room2.id
                }
            ]
        }
        self.assertDictEqual(content, expected)


class ChatTests(TestCase, tests.Utilities):
    def test_volunteer_event_chat_register(self):
        self.skipTest("Not Implemented. When a volunteer signs up for an event, they should be added to the room")

    def test_volunteer_event_chat_unregister(self):
        self.skipTest("Not Implemented. When a volunteer unregisters for an event, they should be removed from the group.")

    def test_message(self):
        self.skipTest("Not Implemented.")

    def test_private_chat(self):
        self.skipTest("Not Implemented.")
