"""
Tests for the Tag API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAG_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create + return a Tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpwd123'):
    """Create + return a new User."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required to GET Tags."""

        resp = self.client.get(TAG_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test an authenticated User can GET a list of Tags."""

        Tag.objects.create(user=self.user, name='healthy')
        Tag.objects.create(user=self.user, name='quick')

        resp = self.client.get(TAG_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(resp.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test an authenticated User can only GET their list of Tags."""

        another_user = create_user(email='anotheruser@example.com',
                                   password='testpwd321')

        Tag.objects.create(user=another_user, name='healthy')
        auth_user_tag = Tag.objects.create(user=self.user, name='quick')

        resp = self.client.get(TAG_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], auth_user_tag.name)
        self.assertEqual(resp.data[0]['id'], auth_user_tag.id)

    def test_updating_tag(self):
        """Test updating a Tag."""

        tag = Tag.objects.create(user=self.user, name='healthy')

        data = {'name': 'quick'}
        resp = self.client.patch(detail_url(tag.id), data=data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, data['name'])

    def test_deleting_tag(self):
        """Test deleting a Tag."""

        tag = Tag.objects.create(user=self.user, name='healthy')

        resp = self.client.delete(detail_url(tag.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing Tags which are assigned to a given Recipe."""

        tag_1 = Tag.objects.create(user=self.user, name='quick')
        tag_2 = Tag.objects.create(user=self.user, name='healthy')

        recipe = Recipe.objects.create(
            title='Greek Salad',
            time_minutes=15,
            price=Decimal('7.50'),
            user=self.user,
        )
        recipe.tags.add(tag_1)

        resp = self.client.get(TAG_URL, {'assign_only': 1})

        serializer_1 = TagSerializer(tag_1)
        serializer_2 = TagSerializer(tag_2)
        self.assertIn(serializer_1.data, resp.data)
        self.assertNotIn(serializer_2.data, resp.data)

    def test_filtered_tags_unique(self):
        """Test that a unique list of filtered Tags is returned."""

        tag = Tag.objects.create(user=self.user, name='healthy')
        Tag.objects.create(user=self.user, name='quick')

        recipe_1 = Recipe.objects.create(
            title='Greek Salad',
            time_minutes=15,
            price=Decimal('7.50'),
            user=self.user,
        )
        recipe_2 = Recipe.objects.create(
            title='Cereal',
            time_minutes=1,
            price=Decimal('2.50'),
            user=self.user,
        )
        recipe_1.tags.add(tag)
        recipe_2.tags.add(tag)

        resp = self.client.get(TAG_URL, {'assign_only': 1})
        self.assertEqual(len(resp.data), 1)
