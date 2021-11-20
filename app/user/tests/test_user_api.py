from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)  # type: ignore


def create_payload():
    return {"email": "test@test.com", "password": "testpassword"}


class PublicUserApiTest(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""

        payload = {
            "email": "stupidtest@test.com",
            "password": "Ttestpasswd123",
            "name": "Test name",
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)  # type: ignore
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)  # type: ignore

    def test_user_exists(self):
        """Test creating user that alrady exists fails"""
        payload = {"email": "test@test.com", "password": "password"}

        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 chars"""
        payload = {"email": "test@test.com", "password": "pas"}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        payload = create_payload()
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)  # type: ignore
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(**create_payload())
        wrong_payload = {"email": "test@test.com", "password": "wrongpassword"}

        res = self.client.post(TOKEN_URL, wrong_payload)

        self.assertNotIn("token", res.data)  # type: ignore
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exists"""

        payload = create_payload()

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)  # type: ignore
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_password_given(self):
        """Test that token is not created if password is not provided"""

        create_user(**create_payload())
        wrong_payload = {"email": "test@test.com", "password": None}

        res = self.client.post(TOKEN_URL, wrong_payload)

        self.assertNotIn("token", res.data)  # type: ignore
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retreive_user_unatuthorized(self):
        """Test that authentication is required for users"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(email="test@test.com", password="testpass", name="name")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retreive_profile_success(self):
        """Test retreiving profile for logged in user"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"name": self.user.name, "email": self.user.email})  # type: ignore

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the url"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = create_payload()
        payload["name"] = "test"
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        # self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
