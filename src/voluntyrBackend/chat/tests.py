import json
import copy
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import RequestsClient

from api import tests
from api.models import EndUser, Event

from chat.models import Room, Membership


class Utilities(tests.Utilities):
    def to_dict(self, response):
        return json.loads(str(response.content, encoding='utf-8'))

    def to_json(self, d):
        return json.dumps(d)

    def get_chat_rooms(self, token):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + token})
        path = 'http://testserver/chat/rooms/'

        response = client.get(path)
        status = response.status_code
        self.assertEqual(status, 200, 'Utility: Get Chat Rooms')
        content = self.to_dict(response)
        return content


# https://channels.readthedocs.io/en/latest/tutorial/part_4.html
class RoomTests(TestCase, Utilities):
    volunteerDicts = [
        {
            'email': 'testemail2019@gmail.com',
            'password': 'testpassword2',
            'first_name': 'First user',
            'last_name': 'volunteer',
            'phone_number': '765-426-4540',
            'birthday': '1998-06-12'
        },
        {
            'email': 'testemail2018@gmail.com',
            'password': 'testpassword2',
            'first_name': 'Second User',
            'last_name': 'volunteer',
            'phone_number': '765-426-2349',
            'birthday': '1998-06-12'
        },
        {
            'email': 'testemail2014@gmail.com',
            'password': 'testpassword2',
            'first_name': 'Third User',
            'last_name': 'volunteer',
            'phone_number': '765-426-5293',
            'birthday': '1998-06-12'
        }
    ]
    volunteerTokens = []

    organization_dict = {
        'email': 'testorgemail5@gmail.com',
        'password': 'testpassword123',
        'name': 'testOrg1',
        'street_address': '1 IU st',
        'city': 'Bloomington',
        'state': 'Indiana',
        'phone_number': '765-426-6891',
        'organization_motto': 'The motto'
    }
    organization_tokens = {}

    event_dict = {
        'start_time': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S%z'),
        'end_time': (timezone.now() + timedelta(days=1, hours=1)).strftime('%Y-%m-%dT%H:%M:%S%z'),
        'date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'title': 'testActivity',
        'location': 'SICE',
        'description': 'testing endpoint'
    }

    def setUp(self):
        self.organization_signup(self.organization_dict)
        self.organization_tokens = self.organization_login(self.organization_dict)
        for volunteer in self.volunteerDicts:
            self.volunteer_signup(volunteer)
            self.volunteerTokens.append(self.volunteer_login(volunteer))

    def test_create_private_chat(self):
        path = 'http://testserver/chat/rooms/'
        rooms_before_new_event = Room.objects.all().count()
        client = RequestsClient()

        user1 = self.volunteerDicts[0]
        user2 = self.volunteerDicts[1]
        user3 = self.volunteerDicts[2]
        user1_token = self.volunteerTokens[0]['access']
        self._test_create_private_chat_helper(user1, user2, user3, user1_token, client, path, rooms_before_new_event, 1)

        user1 = self.volunteerDicts[1]
        user2 = self.volunteerDicts[2]
        user3 = self.volunteerDicts[0]
        user1_token = self.volunteerTokens[1]['access']
        self._test_create_private_chat_helper(user1, user2, user3, user1_token, client, path, rooms_before_new_event, 2)

        room_count = Room.objects.all().count()
        self._test_create_private_chat_helper(user1, user2, user3, user1_token, client, path, rooms_before_new_event, 2)
        self.assertEqual(Room.objects.all().count(), room_count)

    def _test_create_private_chat_helper(self, user1, user2, user3, user1_token, client, path, start_room_count,
                                         room_count_diff):
        client.headers.update({'Authorization': 'Bearer ' + user1_token})

        response = client.post(url=path, data={'email': user2['email']})
        status = response.status_code
        self.assertEqual(status, 201)
        self.assertEqual(Room.objects.all().count(), start_room_count + room_count_diff, 'Chat room creation failed')

        content = self.to_dict(response)
        self.assertIn('id', content)
        room = Room.objects.get(id=content['id'])
        self.assertIn('name', content)
        self.assertEqual(room.get_room_name(), content['name'])
        members = room.members.all()
        self.assertEqual(members.count(), 2)
        self._assert_private_chat_room(room)
        self.assertIn(EndUser.objects.get(email=user1['email']), members)
        self.assertIn(EndUser.objects.get(email=user2['email']), members)
        self.assertNotIn(EndUser.objects.get(email=user3['email']), members)

    def test_create_event_chat(self):
        rooms_before_new_event = Room.objects.all().count()
        self.organization_new_event(self.organization_tokens['access'], self.event_dict)
        rooms_after_new_event = Room.objects.all().count()

        self.assertEqual(rooms_after_new_event, rooms_before_new_event + 1, 'Chat room creation failed')

        actual_room = self.get_chat_rooms(self.organization_tokens['access'])[0]

        room = Room.objects.get(event__id=1)
        self._assert_event_room_name(room.id, self.event_dict['title'])
        self.assertEqual(room.members.all().count(), 1)

        expected_room_dict = {'id': str(room.id), 'name': room.get_room_name()}
        self.assertDictEqual(actual_room, expected_room_dict)

    def test_edit_event_name(self):
        self.organization_new_event(self.organization_tokens['access'], self.event_dict)
        event = Event.objects.get(title=self.event_dict['title'])
        pre_edit_room = Room.objects.get(event=event)
        pre_edit_members = pre_edit_room.members.all()
        self._assert_event_room_name(pre_edit_room.id, event.title)

        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organization_tokens['access']})
        path = 'http://testserver/api/organization/updateEvent/'
        updates = copy.deepcopy(self.event_dict)
        updates['title'] = 'New Title Update'
        updates['id'] = 1
        edit_event_response = client.put(path, json=updates)
        self.assertEqual(edit_event_response.status_code, 201, msg='Failed to edit event: ' + str(updates))

        after_edit_room = Room.objects.get(event__id=event.id)
        self._assert_event_room_name(after_edit_room.id, updates["title"])
        self.assertEqual(list(after_edit_room.members.all()), list(pre_edit_members))

    def test_get_rooms(self):
        client = RequestsClient()
        client.headers.update({'Authorization': 'Bearer ' + self.organization_tokens['access']})
        path = 'http://testserver/chat/rooms/'
        end_user = EndUser.objects.get(id=1)

        self.room1 = Room.objects.create()
        Membership.objects.create(end_user=end_user, room=self.room1)

        self.room2 = Room.objects.create()
        Membership.objects.create(end_user=end_user, room=self.room2)

        self.room3 = Room.objects.create()

        self.failIf(self.organization_tokens is None or len(self.organization_tokens.keys()) != 2,
                    msg='Org Tokens Dict: ' + str(self.organization_tokens.keys()))

        response = client.get(path)
        status = response.status_code
        self.assertEqual(status, 200, 'Utility: Get Chat Rooms')
        content = self.to_dict(response)

        expected = [
            {
                'name': 'Private Chat Room',
                'id': str(self.room1.id)
            },
            {
                'name': 'Private Chat Room',
                'id': str(self.room2.id)
            }
        ]
        self.assertEqual(len(content), len(expected))
        for i in range(0, len(expected)):
            a = content[i]
            e = expected[i]
            self.assertIn(e['name'], a['name'])
            self.assertEqual(a['id'], e['id'])

    def test_volunteer_event_chat_registration(self):
        self.organization_new_event(self.organization_tokens['access'], self.event_dict)
        volunteer = self.volunteerDicts[0]
        volunteer_token = self.volunteerTokens[0]['access']

        self._assert_volunteer_not_in_room(volunteer['email'], 1)
        self._assert_room_member_count(1, 1)
        self.volunteer_signup_for_event(volunteer_token, 1)
        self._assert_volunteer_in_room(volunteer['email'], 1)
        self._assert_room_member_count(1, 2)
        self._assert_volunteer_not_in_room(self.volunteerDicts[1]['email'], 1)
        self._assert_volunteer_not_in_room(self.volunteerDicts[2]['email'], 1)

        volunteer = self.volunteerDicts[1]
        volunteer_token = self.volunteerTokens[1]['access']

        self._assert_volunteer_not_in_room(volunteer['email'], 1)
        self.volunteer_signup_for_event(volunteer_token, 1)
        self._assert_volunteer_in_room(volunteer['email'], 1)
        self._assert_room_member_count(1, 3)
        self._assert_volunteer_in_room(self.volunteerDicts[0]['email'], 1)
        self._assert_volunteer_not_in_room(self.volunteerDicts[2]['email'], 1)

        volunteer = self.volunteerDicts[0]
        volunteer_token = self.volunteerTokens[0]['access']

        self._assert_volunteer_in_room(volunteer['email'], 1)
        self.volunteer_signup_for_event(volunteer_token, 1, unregisting=True)
        self._assert_room_member_count(1, 3)
        self._assert_volunteer_not_attending(volunteer['email'], 1)
        self._assert_volunteer_in_room(self.organization_dict['email'], 1)
        self._assert_volunteer_in_room(self.volunteerDicts[1]['email'], 1)
        self._assert_volunteer_not_in_room(self.volunteerDicts[2]['email'], 1)

    def _assert_event_room_name(self, room_id, event_title):
        room = Room.objects.get(id=room_id)
        self.assertEqual(room.get_room_name(), 'Event Chat Room for ' + event_title)

    def _assert_room_member_count(self, event_id, expected):
        room = Room.objects.get(event__id=event_id)
        self.assertEqual(room.members.all().count(), expected)

    def _assert_volunteer_not_in_room(self, email, event_id):
        end_user = EndUser.objects.get(email=email)
        room = Room.objects.get(event__id=event_id)
        self.assertNotIn(end_user, room.members.all())

    def _assert_volunteer_not_attending(self, email, event_id):
        room = Room.objects.get(event__id=event_id)
        self.failIf(Membership.objects.filter(end_user__email=email, room=room).count() == 0)
        self.assertFalse(Membership.objects.get(end_user__email=email, room=room).attending)

    def _assert_volunteer_in_room(self, email, event_id):
        end_user = EndUser.objects.get(email=email)
        room = Room.objects.get(event__id=event_id)
        self.assertIn(end_user, room.members.all())
        self.assertTrue(Membership.objects.get(end_user=end_user, room=room).attending)

    def _assert_private_chat_room(self, room):
        self.assertIsNone(room.event)
        self.assertIn('Private Chat Room', room.get_room_name())
