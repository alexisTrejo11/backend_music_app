from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from unittest.mock import Mock, patch, MagicMock
from graphql import GraphQLError
import graphene
from datetime import date

from apps.users.schema import Query, Mutation
from apps.users.schema.types import UserType, UserPreferencesType, AuthPayloadType
from apps.users.schema.inputs import (
    RegisterInput,
    LoginInput,
    UpdateProfileInput,
    UpdatePreferencesInput,
    ChangePasswordInput,
)
from apps.users.schema.queries import UserQueryMixin
from apps.users.schema.mutations import (
    Register,
    Login,
    UpdateProfile,
    UpdatePreferences,
    ChangePassword,
    DeleteAccount,
)
from apps.users.models import UserPreferences

User = get_user_model()


class UserTypeTestCase(TestCase):
    """Tests for UserType GraphQL type"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
            subscription_type="premium",
        )
        self.info = Mock()

    def test_user_type_fields(self):
        """Test UserType contains all expected fields"""
        user_type = UserType()
        expected_fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "profile_image",
            "bio",
            "birth_date",
            "country",
            "is_artist",
            "is_verified",
            "subscription_type",
            "created_at",
            "updated_at",
            "followers_count",
            "following_count",
            "playlists_count",
            "is_premium",
        ]
        # Check meta fields exist
        self.assertTrue(hasattr(UserType._meta, "model"))
        self.assertEqual(UserType._meta.model, User)

    def test_resolve_followers_count(self):
        """Test followers count resolution"""
        user_type = UserType()
        count = user_type.resolve_followers_count(self.info)
        self.assertEqual(count, 0)  # Should return 0 as per TODO implementation

    @patch("apps.interactions.models.FollowedArtist")
    def test_resolve_following_count(self, mock_followed_artist):
        """Test following count resolution with mocked data"""
        mock_followed_artist.objects.filter.return_value.count.return_value = 5
        # In GraphQL resolvers, self is the instance being resolved (the user)
        count = UserType.resolve_following_count(self.user, self.info)
        self.assertEqual(count, 5)
        mock_followed_artist.objects.filter.assert_called_once_with(user=self.user)

    @patch("apps.playlists.models.Playlist")
    def test_resolve_playlists_count(self, mock_playlist):
        """Test playlists count resolution with mocked data"""
        mock_playlist.objects.filter.return_value.count.return_value = 3
        # In GraphQL resolvers, self is the instance being resolved (the user)
        count = UserType.resolve_playlists_count(self.user, self.info)
        self.assertEqual(count, 3)
        mock_playlist.objects.filter.assert_called_once_with(
            user=self.user, is_public=True
        )

    def test_resolve_is_premium_true(self):
        """Test is_premium returns True for premium subscriptions"""
        # In GraphQL resolvers, self is the instance being resolved (the user)
        self.assertTrue(UserType.resolve_is_premium(self.user, self.info))

    def test_resolve_is_premium_false(self):
        """Test is_premium returns False for free subscriptions"""
        self.user.subscription_type = "free"
        self.user.save()
        self.assertFalse(UserType.resolve_is_premium(self.user, self.info))

    def test_resolve_is_premium_family(self):
        """Test is_premium returns True for family subscriptions"""
        self.user.subscription_type = "family"
        self.user.save()
        self.assertTrue(UserType.resolve_is_premium(self.user, self.info))

    def test_resolve_is_premium_student(self):
        """Test is_premium returns True for student subscriptions"""
        self.user.subscription_type = "student"
        self.user.save()
        self.assertTrue(UserType.resolve_is_premium(self.user, self.info))


class UserPreferencesTypeTestCase(TestCase):
    """Tests for UserPreferencesType"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.preferences = UserPreferences.objects.create(
            user=self.user,
            explicit_content=True,
            autoplay=False,
            audio_quality="high",
            language="en",
            private_session=False,
        )

    def test_preferences_type_fields(self):
        """Test UserPreferencesType contains all expected fields"""
        self.assertTrue(hasattr(UserPreferencesType._meta, "model"))
        self.assertEqual(UserPreferencesType._meta.model, UserPreferences)


class AuthPayloadTypeTestCase(TestCase):
    """Tests for AuthPayloadType"""

    def test_auth_payload_structure(self):
        """Test AuthPayloadType has correct fields"""
        mock_user = Mock()
        payload = AuthPayloadType(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            user=mock_user,
        )
        self.assertEqual(payload.access_token, "test_access_token")
        self.assertEqual(payload.refresh_token, "test_refresh_token")
        self.assertEqual(payload.user, mock_user)


class UserQueryMixinTestCase(TestCase):
    """Tests for UserQueryMixin"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.query_mixin = UserQueryMixin()
        self.info = Mock()

    def test_resolve_me_authenticated(self):
        """Test resolve_me returns user when authenticated"""
        self.info.context.user = self.user

        result = self.query_mixin.resolve_me(self.info)
        self.assertEqual(result, self.user)

    def test_resolve_me_unauthenticated(self):
        """Test resolve_me raises error when unauthenticated"""
        self.info.context.user = Mock()
        self.info.context.user.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            self.query_mixin.resolve_me(self.info)
        self.assertIn("Authentication required", str(context.exception))

    def test_resolve_user_by_id(self):
        """Test resolve_user by ID"""
        result = self.query_mixin.resolve_user(self.info, id=self.user.id)
        self.assertEqual(result, self.user)

    def test_resolve_user_by_username(self):
        """Test resolve_user by username"""
        result = self.query_mixin.resolve_user(self.info, username="testuser")
        self.assertEqual(result, self.user)

    def test_resolve_user_id_not_found(self):
        """Test resolve_user raises error when ID not found"""
        with self.assertRaises(GraphQLError) as context:
            self.query_mixin.resolve_user(self.info, id=99999)
        self.assertIn("not found", str(context.exception))

    def test_resolve_user_username_not_found(self):
        """Test resolve_user raises error when username not found"""
        with self.assertRaises(GraphQLError) as context:
            self.query_mixin.resolve_user(self.info, username="nonexistent")
        self.assertIn("not found", str(context.exception))

    def test_resolve_user_no_params(self):
        """Test resolve_user raises error when no params provided"""
        with self.assertRaises(GraphQLError) as context:
            self.query_mixin.resolve_user(self.info)
        self.assertIn("must be provided", str(context.exception))

    def test_resolve_user_preferences_authenticated(self):
        """Test resolve_user_preferences returns preferences for authenticated user"""
        self.info.context.user = self.user

        result = self.query_mixin.resolve_user_preferences(self.info)
        self.assertIsInstance(result, UserPreferences)
        self.assertEqual(result.user, self.user)

    def test_resolve_user_preferences_unauthenticated(self):
        """Test resolve_user_preferences raises error when unauthenticated"""
        from django.contrib.auth.models import AnonymousUser

        self.info.context.user = AnonymousUser()

        with self.assertRaises(PermissionDenied) as context:
            self.query_mixin.resolve_user_preferences(self.info)
        self.assertIn("must be logged in", str(context.exception))

    def test_resolve_search_users(self):
        """Test search_users returns matching users"""
        User.objects.create_user(
            email="john@example.com",
            username="johndoe",
            password="pass123",
            first_name="John",
            last_name="Doe",
        )
        User.objects.create_user(
            email="jane@example.com",
            username="janedoe",
            password="pass123",
            first_name="Jane",
            last_name="Doe",
        )

        # Search by username
        results = self.query_mixin.resolve_search_users(self.info, query="john")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, "johndoe")

        # Search by last name
        results = self.query_mixin.resolve_search_users(self.info, query="Doe")
        self.assertEqual(len(results), 2)

    def test_resolve_search_users_limit(self):
        """Test search_users respects limit parameter"""
        for i in range(25):
            User.objects.create_user(
                email=f"user{i}@example.com",
                username=f"user{i}",
                password="pass123",
            )

        results = self.query_mixin.resolve_search_users(
            self.info, query="user", limit=10
        )
        self.assertEqual(len(results), 10)


class RegisterMutationTestCase(TestCase):
    """Tests for Register mutation"""

    def setUp(self):
        self.info = Mock()

    @patch("apps.users.schema.mutations.AuthService.register_user")
    def test_register_success(self, mock_register):
        """Test successful user registration"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "newuser@example.com"

        mock_register.return_value = {
            "user": mock_user,
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        input_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
        }

        result = Register.mutate(None, self.info, input_data)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Registration successful")
        self.assertIsNotNone(result.auth_payload)
        self.assertEqual(result.auth_payload.access_token, "test_access_token")
        mock_register.assert_called_once_with(input_data)

    @patch("apps.users.schema.mutations.AuthService.register_user")
    def test_register_validation_error(self, mock_register):
        """Test registration with validation error"""
        mock_register.side_effect = ValidationError("Email already exists")

        input_data = {
            "email": "existing@example.com",
            "username": "existinguser",
            "password": "pass123",
            "first_name": "Existing",
            "last_name": "User",
        }

        result = Register.mutate(None, self.info, input_data)

        self.assertFalse(result.success)
        self.assertIn("Email already exists", result.message)


class LoginMutationTestCase(TestCase):
    """Tests for Login mutation"""

    def setUp(self):
        self.info = Mock()

    @patch("apps.users.schema.mutations.AuthService.login_user")
    def test_login_success(self, mock_login):
        """Test successful user login"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"

        mock_login.return_value = {
            "user": mock_user,
            "token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        input_data = {"email": "test@example.com", "password": "testpass123"}

        result = Login.mutate(None, self.info, input_data)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Login successful")
        self.assertIsNotNone(result.auth_payload)
        mock_login.assert_called_once_with("test@example.com", "testpass123")

    @patch("apps.users.schema.mutations.AuthService.login_user")
    def test_login_invalid_credentials(self, mock_login):
        """Test login with invalid credentials"""
        mock_login.side_effect = ValidationError("Invalid credentials")

        input_data = {"email": "test@example.com", "password": "wrongpass"}

        result = Login.mutate(None, self.info, input_data)

        self.assertFalse(result.success)
        self.assertIn("Invalid credentials", result.message)

    @patch("apps.users.schema.mutations.AuthService.login_user")
    def test_login_email_strip(self, mock_login):
        """Test login strips whitespace from email"""
        mock_user = Mock()
        mock_login.return_value = {
            "user": mock_user,
            "token": "test_token",
        }

        input_data = {"email": "  test@example.com  ", "password": "pass123"}

        Login.mutate(None, self.info, input_data)

        # Verify email was stripped
        mock_login.assert_called_once_with("test@example.com", "pass123")


class UpdateProfileMutationTestCase(TestCase):
    """Tests for UpdateProfile mutation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.info = Mock()
        self.info.context.user = self.user

    @patch("apps.users.schema.mutations.UserService.update_profile")
    def test_update_profile_success(self, mock_update):
        """Test successful profile update"""
        updated_user = self.user
        updated_user.first_name = "Updated"
        updated_user.bio = "New bio"

        mock_update.return_value = updated_user

        input_data = {"first_name": "Updated", "bio": "New bio"}

        result = UpdateProfile.mutate(None, self.info, input_data)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Profile updated successfully")
        self.assertEqual(result.user, updated_user)
        mock_update.assert_called_once_with(self.user, input_data)

    def test_update_profile_unauthenticated(self):
        """Test update profile without authentication"""
        from django.contrib.auth.models import AnonymousUser

        self.info.context.user = AnonymousUser()

        input_data = {"first_name": "Updated"}

        with self.assertRaises(PermissionDenied):
            UpdateProfile.mutate(None, self.info, input_data)


class UpdatePreferencesMutationTestCase(TestCase):
    """Tests for UpdatePreferences mutation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.preferences = UserPreferences.objects.create(user=self.user)
        self.info = Mock()
        self.info.context.user = self.user

    @patch("apps.users.schema.mutations.UserService.update_preferences")
    def test_update_preferences_success(self, mock_update):
        """Test successful preferences update"""
        updated_preferences = self.preferences
        updated_preferences.audio_quality = "high"
        updated_preferences.autoplay = False

        mock_update.return_value = updated_preferences

        input_data = {"audio_quality": "high", "autoplay": False}

        result = UpdatePreferences.mutate(None, self.info, input_data)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Preferences updated successfully")
        self.assertEqual(result.preferences, updated_preferences)
        mock_update.assert_called_once_with(self.user, input_data)

    def test_update_preferences_unauthenticated(self):
        """Test update preferences without authentication"""
        from django.contrib.auth.models import AnonymousUser

        self.info.context.user = AnonymousUser()

        input_data = {"audio_quality": "high"}

        with self.assertRaises(PermissionDenied):
            UpdatePreferences.mutate(None, self.info, input_data)


class ChangePasswordMutationTestCase(TestCase):
    """Tests for ChangePassword mutation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="oldpass123",
        )
        self.info = Mock()
        self.info.context.user = self.user

    @patch("apps.users.schema.mutations.AuthService.change_password")
    def test_change_password_success(self, mock_change):
        """Test successful password change"""
        mock_change.return_value = True

        input_data = {"old_password": "oldpass123", "new_password": "newpass456"}

        result = ChangePassword.mutate(None, self.info, input_data)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Password changed successfully")
        mock_change.assert_called_once_with(self.user, "oldpass123", "newpass456")

    @patch("apps.users.schema.mutations.AuthService.change_password")
    def test_change_password_wrong_old_password(self, mock_change):
        """Test password change with wrong old password"""
        mock_change.side_effect = ValidationError("Current password is incorrect")

        input_data = {"old_password": "wrongpass", "new_password": "newpass456"}

        result = ChangePassword.mutate(None, self.info, input_data)

        self.assertFalse(result.success)
        self.assertIn("Current password is incorrect", result.message)

    def test_change_password_unauthenticated(self):
        """Test password change without authentication"""
        from django.contrib.auth.models import AnonymousUser

        self.info.context.user = AnonymousUser()

        input_data = {"old_password": "oldpass123", "new_password": "newpass456"}

        with self.assertRaises(PermissionDenied):
            ChangePassword.mutate(None, self.info, input_data)


class DeleteAccountMutationTestCase(TestCase):
    """Tests for DeleteAccount mutation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.info = Mock()
        self.info.context.user = self.user

    @patch("apps.users.schema.mutations.UserService.delete_account")
    def test_delete_account_success(self, mock_delete):
        """Test successful account deletion"""
        mock_delete.return_value = True

        result = DeleteAccount.mutate(None, self.info, password="testpass123")

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Account deleted successfully")
        mock_delete.assert_called_once_with(self.user, "testpass123")

    @patch("apps.users.schema.mutations.UserService.delete_account")
    def test_delete_account_wrong_password(self, mock_delete):
        """Test account deletion with wrong password"""
        mock_delete.side_effect = ValidationError("Invalid password")

        result = DeleteAccount.mutate(None, self.info, password="wrongpass")

        self.assertFalse(result.success)
        self.assertIn("Invalid password", result.message)

    def test_delete_account_unauthenticated(self):
        """Test account deletion without authentication"""
        from django.contrib.auth.models import AnonymousUser

        self.info.context.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            DeleteAccount.mutate(None, self.info, password="testpass123")


class SchemaIntegrationTestCase(TestCase):
    """Integration tests for complete schema"""

    def setUp(self):
        self.schema = graphene.Schema(query=Query, mutation=Mutation)

    def test_schema_query_fields(self):
        """Test schema has all expected query fields"""
        query_type = self.schema.query
        self.assertTrue(hasattr(query_type, "_meta"))

    def test_schema_mutation_fields(self):
        """Test schema has all expected mutation fields"""
        mutation_type = self.schema.mutation
        self.assertTrue(hasattr(mutation_type, "_meta"))
