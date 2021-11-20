from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email="test@test.com", password="testpass"):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)  # type: ignore


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = "test@test.com"
        password = "Testpass123"
        user = get_user_model().objects.create_user(email=email, password=password)  # type: ignore

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normilized(self):
        """Test the email for a new user is normalizer"""

        email = "test@TEST.COM"

        user = get_user_model().objects.create_user(email, "test123")  # type: ignore

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email rases error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "test123")  # type: ignore

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser("test@test.com", "test123")  # type: ignore
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""

        tag = models.Tag.objects.create(user=sample_user(), name="Vegan")
        self.assertEqual(str(tag), tag.name)

    def test_ingridient_str(self):
        """Test the ingridient string representation"""

        ingridient = models.Ingredient.objects.create(
            user=sample_user(), name="Cucumber"
        )

        self.assertEqual(str(ingridient), ingridient.name)

    def test_recipe_str(self):
        """Test the recipe string representation"""

        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title="Steak and mushroom sause",
            time_minutes=5,
            price=5.00,
        )

        self.assertEqual(str(recipe), recipe.title)
