from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from core.models import Recipe
from recipe.serializers import RecipeSerializer  # type: ignore

RECIPE_URL = reverse("recipe:recipe-list")


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {"title": "Sample recipe", "time_minutes": 10, "price": 5.00}
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required"""

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = get_user_model().objects.create(
            email="test@test.com", password="password"
        )
        self.client.force_authenticate(self.user)

    def test_retreive_recipe(self):
        """Test retreiving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user, title="Second recipe")

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_recipes_limited_to_user(self):
        """Test that recipes limited to authenticatd user"""
        sample_recipe(user=self.user)
        user2 = get_user_model().objects.create(
            email="test2@gmail.com", password="password"
        )
        sample_recipe(user=user2, title="Another title")

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type: ignore
        self.assertEqual(res.data, serializer.data)  # type: ignore