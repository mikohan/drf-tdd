import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer  # type: ignore
from django.db.models.query import QuerySet

RECIPE_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id: int) -> str:
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name="Main cource"):
    """Create and return sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    """Create and return sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


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

    def test_view_recipe_detail(self):
        """Test veiwing a recipe detail"""

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {"title": "Chocolate cheeskake", "time_minutes": 20, "price": 5.00}
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""

        tag1: "QuerySet[Tag]" = sample_tag(user=self.user, name="Vegan")
        tag2: "QuerySet[Tag]" = sample_tag(user=self.user, name="Dessert")

        payload = {
            "title": "Avocado lime cheescake",
            "tags": [tag1.id, tag2.id],  # type: ignore
            "time_minutes": 60,
            "price": 20.00,
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""

        ingr1: "QuerySet[Ingredient]" = sample_ingredient(
            user=self.user, name="Cucumber"
        )
        ingr2: "QuerySet[Ingredient]" = sample_ingredient(user=self.user, name="Kale")

        payload = {
            "title": "Avocado lime cheescake",
            "ingredients": [ingr1.id, ingr2.id],  # type: ignore
            "time_minutes": 60,
            "price": 20.00,
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])  # type: ignore
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingr1, ingredients)
        self.assertIn(ingr2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Curry")

        payload = {"title": "Chicken tikka", "tags": [new_tag.id]}  # type: ignore

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {"title": "Spagetti carboanra", "time_minutes": 25, "price": 5.00}
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_minutes, payload["time_minutes"])
        self.assertEqual(recipe.price, payload["price"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)


class RecipeImageUploadTests(TestCase):
    """Testing image uploading"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(  # type: ignore
            email="user@test.com", password="testpass"
        )

        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn("image", res.data)  # type: ignore
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an inalid image"""

        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tag(self):
        """Test returning recipes with sepecific tags"""

        recipe1 = sample_recipe(user=self.user, title="Thai vegetable carry")
        recipe2 = sample_recipe(user=self.user, title="Aubergine with tahini")
        tag1 = sample_tag(user=self.user, name="Vegan")
        tag2 = sample_tag(user=self.user, name="Vegetarian")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title="Fish and chips")

        res = self.client.get(RECIPE_URL, {"tags": f"{tag1.id},{tag2.id}"})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)  # type: ignore
        self.assertIn(serializer2.data, res.data)  # type: ignore
        self.assertNotIn(serializer3.data, res.data)  # type: ignore

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingridients"""
        recipe1 = sample_recipe(user=self.user, title="Posh beans on toast")
        recipe2 = sample_recipe(user=self.user, title="Chicken cacciatore")
        ingredient1 = sample_ingredient(user=self.user, name="Feta cheese")
        ingredient2 = sample_ingredient(user=self.user, name="Chicken")
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title="Steak and mashrooms")

        res = self.client.get(
            RECIPE_URL, {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)  # type: ignore
        self.assertIn(serializer2.data, res.data)  # type: ignore
        self.assertNotIn(serializer3.data, res.data)  # type: ignore
