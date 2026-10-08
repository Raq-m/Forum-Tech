from django.contrib.auth import get_user_model
from django.test import TestCase


User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="secure-password",
        )

        self.assertEqual(
            user.username,
            "testuser",
        )
        self.assertEqual(
            user.email,
            "test@example.com",
        )
        self.assertTrue(
            user.check_password(
                "secure-password"
            )
        )
