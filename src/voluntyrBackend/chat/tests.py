from django.test import TestCase


# https://channels.readthedocs.io/en/latest/tutorial/part_4.html
class ChatTests(TestCase):
    def test_create_event_chat(self):
        self.skipTest("Not Implemented. When an event is created, a chat room should also be created with the organization as the only a member.")

    def test_volunteer_event_chat_register(self):
        self.skipTest("Not Implemented. When a volunteer signs up for an event, they should be added to the room")

    def test_volunteer_event_chat_unregister(self):
        self.skipTest("Not Implemented. When a volunteer unregisters for an event, they should be removed from the group.")

    def test_message(self):
        self.skipTest("Not Implemented.")

    def test_private_chat(self):
        self.skipTest("Not Implemented.")
