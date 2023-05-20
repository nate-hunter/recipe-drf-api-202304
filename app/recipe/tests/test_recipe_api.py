"""
Tests for the Recipe API.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create + return a Recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Helper function to create and return a test recipe."""

    default_data = {
        'title': 'Test Recipe Title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Test recipe description',
        'link': 'http://example.com/recipe.pdf',
    }
    default_data.update(params)

    recipe = Recipe.objects.create(user=user, **default_data)
    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test whether authentication is required to call API."""

        resp = self.client.get(RECIPES_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpwd123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test an authenticated User can GET a list of Recipes."""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        resp = self.client.get(RECIPES_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(resp.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test an authenticated User only GETs their list of Recipes."""

        other_user = get_user_model().objects.create_user(
            'otheruser@test.com',
            'testpwd321',
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        resp = self.client.get(RECIPES_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(resp.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test GET recipe detail."""
        recipe = create_recipe(user=self.user)

        resp = self.client.get(detail_url(recipe.id))

        # serializer = RecipeSerializer(recipe)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(resp.data, serializer.data)
