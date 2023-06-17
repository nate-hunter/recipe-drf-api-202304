"""
Tests for the Ingredient API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create + return an Ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


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

    def test_update_ingredient(self):
        """Test an Ingredient can be updated."""

        ingredient = Ingredient.objects.create(user=self.user, name='garlic')

        data = {'name': 'onion'}
        url = detail_url(ingredient.id)
        resp = self.client.patch(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, data['name'])

    def test_deleting_ingredient(self):
        """Test an Ingredient can be deleted."""

        ingredient = Ingredient.objects.create(user=self.user, name='garlic')
        url = detail_url(ingredient.id)
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.all()
        self.assertEqual(ingredients.count(), 0)

        # ingredients = Ingredient.objects.filter(user=self.user)
        # self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing Ingredients which are assigned to a given Recipe."""

        ingredient_1 = Ingredient.objects.create(user=self.user, name='onion')
        ingredient_2 = Ingredient.objects.create(user=self.user, name='garlic')

        recipe = Recipe.objects.create(
            title='Greek Salad',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )
        recipe.ingredients.add(ingredient_1)

        resp = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer_1 = IngredientSerializer(ingredient_1)
        serializer_2 = IngredientSerializer(ingredient_2)
        self.assertIn(serializer_1.data, resp.data)
        self.assertNotIn(serializer_2.data, resp.data)

    def test_filtered_ingredients_unique(self):
        """Test that a unique list of filtered Ingredients is returned."""
        ingredient = Ingredient.objects.create(user=self.user, name='onion')
        Ingredient.objects.create(user=self.user, name='garlic')

        recipe_1 = Recipe.objects.create(
            title='Greek Salad',
            time_minutes=10,
            price=Decimal('5.50'),
            user=self.user,
        )
        recipe_2 = Recipe.objects.create(
            title='Kimchee Fried Rice',
            time_minutes=15,
            price=Decimal('10.50'),
            user=self.user,
        )

        recipe_1.ingredients.add(ingredient)
        recipe_2.ingredients.add(ingredient)

        resp = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(resp.data), 1)
