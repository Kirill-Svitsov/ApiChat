from django.test import TestCase
from users.models import User
from messenger.models import Chat, Message


class BaseTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username='user1',
            email='user1@gmail.com',
            first_name='User',
            last_name='One'
        )
        self.user2 = User.objects.create(
            username='user2',
            email='user2@gmail.com',
            first_name='User',
            last_name='Two'
        )
        self.chat = Chat.objects.create(
            sender=self.user1,
            recipient=self.user2
        )
        self.message = Message.objects.create(
            chat=self.chat,
            author=self.user1,
            text='Hello'
        )


class ChatModelTest(BaseTest):
    def test_chat_creation(self):
        self.assertEqual(self.chat.sender, self.user1)
        self.assertEqual(self.chat.recipient, self.user2)


class MessageModelTest(BaseTest):

    def test_message_creation(self):
        self.assertEqual(self.message.chat, self.chat)
        self.assertEqual(self.message.author, self.user1)
        self.assertEqual(self.message.text, 'Hello')
