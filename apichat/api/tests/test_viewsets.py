from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, force_authenticate

from users.models import User
from messenger.models import Chat, Message, Image


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
        self.user3 = User.objects.create(
            username='user3',
            email='user3@gmail.com',
            first_name='User',
            last_name='Three'
        )
        self.client_user1 = APIClient()
        self.client_user2 = APIClient()
        self.client_user3 = APIClient()
        self.client_user1.force_authenticate(user=self.user1)
        self.client_user2.force_authenticate(user=self.user2)
        self.client_user3.force_authenticate(user=self.user3)


class ChatViewSetTests(BaseTest):
    url = '/api/v1/chats/'

    def test_create_chat(self):
        """Тесты на создание чатов"""
        first_data = {'recipient': self.user1.id}
        second_data = {'recipient': self.user2.id}
        third_data = {'recipient': self.user3.id}
        fourth_data = {'recipient': self.client}
        # Создание чата user1 и user2 c id чата = 1
        first_response = self.client_user2.post(self.url, first_data, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        # Попытка подписаться на самого себя
        second_response = self.client_user2.post(self.url, second_data, format='json')
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        # Попытка создать существующий чат тем же юзером
        third_response = self.client_user2.post(self.url, first_data, format='json')
        self.assertEqual(third_response.status_code, status.HTTP_400_BAD_REQUEST)
        # Попытка создать существующий чат вторым участником
        fourth_response = self.client_user1.post(self.url, second_data, format='json')
        self.assertEqual(fourth_response.status_code, status.HTTP_400_BAD_REQUEST)
        # Создание чата между user1 и user3 с id чата = 2
        fifth_response = self.client_user1.post(self.url, third_data, format='json')
        self.assertEqual(fifth_response.status_code, status.HTTP_201_CREATED)

    def test_get_chats(self):
        """Тесты на получение чатов"""
        # Получение своих чатов user1
        first_response = self.client_user1.get(self.url)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        # Получение своих чатов user2
        second_response = self.client_user2.get(self.url)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        # Получение своих чатов user3
        third_response = self.client_user3.get(self.url)
        self.assertEqual(third_response.status_code, status.HTTP_200_OK)
        # Получение чатов анонимом
        anonymous_response = self.client.get(self.url)
        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_chat_by_id(self):
        """Тесты на получение чата по id"""
        # Создаем чат между user1 и user2
        chat = self.client_user1.post(
            self.url,
            {'recipient': self.user2.id}, format='json'
        )
        # Получаем идентификатор созданного чата
        chat_id = chat.data.get('id')
        # Запрос от user1 к чату с user2
        first_response = self.client_user1.get(f'{self.url}{chat_id}/')
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        # Запрос от user2 к чату с user1
        second_response = self.client_user2.get(f'{self.url}{chat_id}/')
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        # Запрос от user3 к чату user1 c user2
        third_response = self.client_user3.get(f'{self.url}{chat_id}/')
        self.assertEqual(third_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_message(self):
        """Тесты на отправление и проверку содержимого сообщений"""
        # Создаем чат между user1 и user2
        chat = self.client_user1.post(
            self.url,
            {'recipient': self.user2.id}, format='json'
        )
        # Получаем идентификатор созданного чата
        chat_id = chat.data.get('id')
        # Отправляем сообщение от user1 к user2
        first_response = self.client_user1.post(
            f'{self.url}{chat_id}/messages/',
            data={'text': 'Hello'},
            format='json'
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        # Отправляем сообщение от user2 к user1
        second_response = self.client_user2.post(
            f'{self.url}{chat_id}/messages/',
            data={'text': 'Hi!'},
            format='json'
        )
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        # Получаем все сообщения чата от пользователя user1
        third_response = self.client_user1.get(f'{self.url}{chat_id}/messages/')
        self.assertEqual(third_response.status_code, status.HTTP_200_OK)
        # Проверяем количество сообщений
        results = third_response.data['results']
        self.assertEqual(len(results), 2)
        # Проверяем содержимое каждого сообщения
        first_message = results[0]
        self.assertEqual(first_message['text'], 'Hi!')
        self.assertEqual(first_message['author']['id'], self.user2.id)
        second_message = results[1]
        self.assertEqual(second_message['text'], 'Hello')
        self.assertEqual(second_message['author']['id'], self.user1.id)
