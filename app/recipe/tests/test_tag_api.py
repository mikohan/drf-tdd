from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer  # type: ignore

TAG_URL = reverse("recipe:tag-list")


def create_payload(email="test@test.com", password="password"):
    return {"email": email, "password": password}


class PublicTagsTests(TestCase):
    """Test the publicity avaliable tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login required for retrieving tags"""

        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsTests(TestCase):
    """Test that authorized user API"""

    def setUp(self):
        self.payload = create_payload()
        self.user = get_user_model().objects.create_user(**self.payload)  # type: ignore
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_tetrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_tags_limited_to_user(self):
        """Test that tags returnend are for the authenticated user"""

        user2 = get_user_model().objects.create_user(email="test2@gmail.com", password="password")  # type: ignore
        Tag.objects.create(user=user2, name="Fuity")

        tag = Tag.objects.create(user=self.user, name="Compfort Food")

        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type: ignore
        self.assertEqual(res.data[0]["name"], tag.name)  # type: ignore
