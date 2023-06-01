"""
Tests for the Recipe API.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

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


def create_user(**params):
    """Create + return a new User."""
    return get_user_model().objects.create_user(**params)


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

        self.user = create_user(
            email='user@example.com',
            password='testpwd123'
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

        other_user = create_user(
            email='otheruser@test.com',
            password='testpwd321'
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

    def test_create_recipe(self):
        """Test creating a recipe."""

        data = {
            'title': 'New Recipe',
            'time_minutes': 25,
            'price': Decimal('12.75')
        }
        resp = self.client.post(RECIPES_URL, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=resp.data['id'])
        for k, v in data.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partially updating a Recipe."""

        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Test Recipe Title',
            link=original_link,
        )

        data = {'title': 'Updated Test Recipe Title'}
        resp = self.client.patch(detail_url(recipe.id), data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, data['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test fully updating a Recipe."""

        recipe = create_recipe(
            user=self.user,
            title='Test Recipe Title',
            link='http://example.com/recipe.pdf',
            description='Test recipe description'
        )

        data = {
            'title': 'Updated Test Recipe Title',
            'link': 'http://example.com/new-recipe.pdf',
            'description': 'Updated test recipe description',
            'price': Decimal(8.25),
            'time_minutes': 8,
        }

        resp = self.client.put(detail_url(recipe.id), data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        for k, v in data.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test error returned when attempting to change the Recipe's User."""

        new_user = create_user(
            email='newuser@example.com',
            password='testpwd321'
        )
        recipe = create_recipe(user=self.user)

        data = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, data)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a Recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test error returned when trying to delete another Users Recipe."""
        new_user = create_user(
            email='newuser@example.com',
            password='testpwd321'
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a Recipt with new Tags."""

        data = {
            'title': 'Greek Salad',
            'time_minutes': 15,
            'price': Decimal('8.50'),
            'tags': [
                {'name': 'Greek'},
                {'name': 'healthy'},
            ]
        }
        resp = self.client.post(RECIPES_URL, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in data['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a Recipe with an existing Tag."""

        tag = Tag.objects.create(user=self.user, name='Greek')

        data = {
            'title': 'Greek Salad',
            'time_minutes': 15,
            'price': Decimal('8.50'),
            'tags': [
                {'name': 'Greek'},
                {'name': 'healthy'},
            ]
        }

        resp = self.client.post(RECIPES_URL, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())

        for tag in data['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test a Tag is created when updating a Recipe."""

        recipe = create_recipe(user=self.user)

        data = {'tags': [{'name': 'healthy'}]}
        resp = self.client.patch(detail_url(recipe.id), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name='healthy')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test updating a Recipe and assiging it an existing Tag."""

        tag_healthy = Tag.objects.create(user=self.user, name='healthy')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_healthy)

        tag_quick = Tag.objects.create(user=self.user, name='quick')
        data = {'tags': [{'name': 'quick'}]}
        resp = self.client.patch(detail_url(recipe.id), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(tag_quick, recipe.tags.all())
        self.assertNotIn(tag_healthy, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing the Tags of a Recipe."""

        tag = Tag.objects.create(user=self.user, name='healthy')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        data = {'tags': []}
        resp = self.client.patch(detail_url(recipe.id), data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a Recipe with new Ingredients."""

        data = {
            'title': 'Greek Salad',
            'time_minutes': 15,
            'price': Decimal('8.50'),
            'ingredients': [
                {'name': 'tomato'},
                {'name': 'onion'},
                {'name': 'olives'},
            ]
        }
        resp = self.client.post(RECIPES_URL, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)

        for ingredient in data['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

        ingredients = Ingredient.objects.all()
        self.assertEqual(len(data['ingredients']), ingredients.count())

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new Recipe with existing Ingredients."""

        ingredient = Ingredient.objects.create(name='onion', user=self.user)

        data = {
            'title': 'Greek Salad',
            'time_minutes': 15,
            'price': Decimal('8.50'),
            'ingredients': [
                {'name': 'tomato'},
                {'name': 'onion'},
                {'name': 'olives'},
            ]
        }
        resp = self.client.post(RECIPES_URL, data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)

        for ingredient in data['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

        ingredients = Ingredient.objects.all()
        self.assertEqual(len(data['ingredients']), ingredients.count())

    def test_create_ingredient_on_update(self):
        """Test creating an Ingredient on Recipe update."""

        recipe = create_recipe(user=self.user)

        data = {'ingredients': [{'name': 'tomato'}]}
        recipe_url = detail_url(recipe.id)
        resp = self.client.patch(recipe_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        ingredient = Ingredient.objects.get(user=self.user, name='tomato')
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test updating a Recipe and assiging it an existing Ingredient."""

        ingredient_onion = Ingredient.objects.create(user=self.user,
                                                     name='onion')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_onion)

        ingredient_garlic = Ingredient.objects.create(user=self.user,
                                                      name='garlic')
        data = {'ingredients': [{'name': 'garlic'}]}
        recipe_url = detail_url(recipe.id)
        resp = self.client.patch(recipe_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient_garlic, recipe.ingredients.all())
        self.assertNotIn(ingredient_onion, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a Recipe's Ingredients."""

        ingredient = Ingredient.objects.create(user=self.user, name='onion')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        self.assertEqual(recipe.ingredients.count(), 1)

        data = {'ingredients': []}
        recipe_url = detail_url(recipe.id)
        resp = self.client.patch(recipe_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
