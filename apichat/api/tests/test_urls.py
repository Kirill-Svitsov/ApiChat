from http import HTTPStatus

from django.test import TestCase


class TestRoutes(TestCase):

    def test_home_page(self):
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
