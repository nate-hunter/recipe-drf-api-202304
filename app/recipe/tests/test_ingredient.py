"""
Tests for the Ingredient API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email='user@example.com', password='testpwd123'):
    """Create + return User."""
    return get_user_model().objects.create(email=email, password=password)


class PublicIngredientApiTest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required to GET Ingredients."""

        resp = self.client.get(INGREDIENTS_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test an authenticated User can GET a list of Ingredients."""

        Ingredient.objects.create(user=self.user, name='garlic')
        Ingredient.objects.create(user=self.user, name='onion')

        resp = self.client.get(INGREDIENTS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(resp.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test an authenticated User can only GET their Ingredients."""

        other_user = create_user(email='otheruser@example.com',
                                 password='testpwd321')

        Ingredient.objects.create(user=other_user, name='onion')
        ingredient = Ingredient.objects.create(user=self.user, name='garlic')

        resp = self.client.get(INGREDIENTS_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], ingredient.id)
        self.assertEqual(resp.data[0]['name'], ingredient.name)
