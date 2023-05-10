"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test that creating a user with an email is successful."""

        email = 'test@example.com'
        password = 'testpwd123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test an email is normalized for new users."""

        data = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, expected_data in data:
            user = get_user_model().objects.create_user(email, 'test123')
            # print(f'[email] {email} -- [expected_data] {expected_data} -- [user] {user}')
            self.assertEqual(user.email, expected_data)

