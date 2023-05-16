"""
Tests for the User API.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    """Create + return a new User."""

    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public/unauthenticated features of the User API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test successfull creation of a User."""

        payload = {
            'email': 'test@example.com',
            'password': 'testpwd123',
            'name': 'JoJo Binkley',
        }
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', resp.data)

    def test_user_with_email_exists_error(self):
        """Test error returned when creating a user with an existing email."""

        payload = {
            'email': 'test@example.com',
            'password': 'testpwd123',
            'name': 'JoJo Binkley',
        }
        create_user(**payload)
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test error returned for a password less than 5 characters."""

        payload = {
            'email': 'test@example.com',
            'password': 'pwd',
            'name': 'JoJo Binkley',
        }
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exclude()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""

        user_details = {
            'name': 'JoJo Binkley',
            'email': 'test@example.com',
            'password': 'testpwd123',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test error returned for invalid password."""

        create_user(email='test@example.com', password='successpwd')

        payload = {
            'email': 'test@example.com',
            'password': 'failpwd',
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test error returned for invalid email."""

        payload = {
            'email': 'test@example.com',
            'password': 'testpwd123',
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test error returned for missing password."""

        payload = {
            'email': 'test@example.com',
            'password': '',
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
