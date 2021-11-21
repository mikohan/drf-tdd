from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer  # type: ignore


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_recipe(user, **kwargs):
    defaults = {"title": "Sample recipe", "time_minutes": 10, "price": 3.00}
    defaults.update(**kwargs)
    return Recipe.objects.create(user=user, **defaults)


class PublicIingredientsTests(TestCase):
    """Test publicly available ingredients api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("test@test.com", "password")  # type: ignore
        self.client.force_authenticate(self.user)

    def test_retreive_ingridient_list(self):
        """Test retreiving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Salt")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_ingredients_limited_to_user(self):
        """Test that ingredients for the authenticated user are returned"""
        user2 = get_user_model().objects.create_user("other@test.com", "testpass")  # type: ignore
        Ingredient.objects.create(user=user2, name="Vinegar")
        ingredient = Ingredient.objects.create(user=self.user, name="Tumeric")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type: ignore
        self.assertEqual(res.data[0]["name"], ingredient.name)  # type: ignore

    def test_create_ingredient_successful(self):
        """Test create a new ingredient"""
        payload = {"name": "Cabbage"}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user, name=payload["name"]
        ).exists()

        self.assertTrue(exists)

    def test_create_ingridient_invalid(self):
        """Test creating invalid ingredient fails"""

        payload = {"name": ""}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        """Test filtering ingredients by those assigned to recipes"""

        ingredient1 = Ingredient.objects.create(user=self.user, name="Cheese")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Kale")

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)  # type: ignore
        self.assertNotIn(serializer2.data, res.data)  # type: ignore

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""

        ingredient = Ingredient.objects.create(user=self.user, name="Meat")
        Ingredient.objects.create(user=self.user, name="Yast")
        recipe1 = create_recipe(user=self.user, title="Perfect stew")
        recipe1.ingredients.add(ingredient)
        recipe2 = create_recipe(user=self.user, title="Good beefstroganoff")
        recipe2.ingredients.add(ingredient)
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)  # type: ignore
