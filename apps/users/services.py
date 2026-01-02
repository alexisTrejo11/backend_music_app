from typing import Dict, Tuple, Any
import re
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import UserPreferences

User = get_user_model()


class AuthService:
    """Service for authentication operations"""

    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 30
    MIN_PASSWORD_LENGTH = 8
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

    @staticmethod
    def _validate_required_fields(data: Dict, required_fields: Tuple) -> None:
        """
        Validate that all required fields are present and non-empty

        Args:
            data: Dictionary with registration data
            required_fields: Tuple of required field names
        """
        for field in required_fields:
            value = data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                raise ValidationError(f"{field.replace('_', ' ').title()} is required")

    @staticmethod
    def _validate_username(username: str) -> None:
        """
        Validate username format and availability

        Args:
            username: Username to validate
        """
        username = username.strip()

        if len(username) < AuthService.MIN_USERNAME_LENGTH:
            raise ValidationError(
                f"Username must be at least {AuthService.MIN_USERNAME_LENGTH} characters long"
            )

        if len(username) > AuthService.MAX_USERNAME_LENGTH:
            raise ValidationError(
                f"Username must not exceed {AuthService.MAX_USERNAME_LENGTH} characters"
            )

        if not AuthService.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already taken")

    @staticmethod
    def _validate_email(email: str) -> None:
        """
        Validate email format and availability

        Args:
            email: Email to validate
        """
        email = email.strip().lower()

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Invalid email format")

        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered")

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        """
        Validate password strength requirements

        Args:
            password: Password to validate
        """
        if len(password) < AuthService.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {AuthService.MIN_PASSWORD_LENGTH} characters long"
            )

        patterns = [
            (r"[A-Z]", "Password must contain at least one uppercase letter"),
            (r"[a-z]", "Password must contain at least one lowercase letter"),
            (r"[0-9]", "Password must contain at least one number"),
        ]

        for pattern, error_message in patterns:
            if not re.search(pattern, password):
                raise ValidationError(error_message)

    @staticmethod
    def register_user(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user

        Args:
            data: Dictionary with registration data

        Returns:
            Dict with user, token, and refresh_token

        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }

        email = cleaned_data.get("email", "").lower()
        username = cleaned_data.get("username", "")
        password = cleaned_data.get("password", "")

        required_fields = (
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "country",
        )
        AuthService._validate_required_fields(cleaned_data, required_fields)
        AuthService._validate_email(email)
        AuthService._validate_username(username)
        AuthService._validate_password_strength(password)

        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                first_name=cleaned_data["first_name"],
                last_name=cleaned_data["last_name"],
                birth_date=cleaned_data["birth_date"],
                country=cleaned_data["country"],
            )

            UserPreferences.objects.create(user=user)

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

    @staticmethod
    def login_user(email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens

        Args:
            email: User email
            password: User password

        Returns:
            Dict with user, token, and refresh_token

        Raises:
            ValidationError: If authentication fails
        """
        email = email.strip().lower()

        if not email or not password:
            raise ValidationError("Email and password are required")

        user = authenticate(username=email, password=password)
        if not user:
            raise ValidationError("Invalid credentials")

        if not user.is_active:
            raise ValidationError("Account is inactive")

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> None:
        """
        Change user password

        Args:
            user: User instance
            old_password: Current password
            new_password: New password

        Raises:
            ValidationError: If validation fails
        """
        if not old_password or not new_password:
            raise ValidationError("Both old and new passwords are required")

        if not user.check_password(old_password):
            raise ValidationError("Current password is incorrect")

        if old_password == new_password:
            raise ValidationError(
                "New password must be different from current password"
            )

        AuthService._validate_password_strength(new_password)

        user.set_password(new_password)
        user.save(update_fields=["password"])

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """
        Refresh JWT access token

        Args:
            refresh_token: Refresh token string

        Returns:
            Dict with new access token and refresh token

        Raises:
            ValidationError: If refresh token is invalid or expired
        """
        if not refresh_token:
            raise ValidationError("Refresh token is required")

        try:
            refresh = RefreshToken(refresh_token)
            # TODO: validate the token type or other claims here
            return {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }
        except Exception as e:
            raise ValidationError("Invalid or expired refresh token")

    @classmethod
    def validate_password(cls, password: str) -> None:
        """
        Public method to validate password strength

        Args:
            password: Password to validate
        """
        cls._validate_password_strength(password)


class UserService:
    """Service for user profile operations"""

    @staticmethod
    def update_profile(user, data: Dict):
        """
        Update user profile

        Args:
            user: User instance
            data: Dictionary with profile data

        Returns:
            Updated user instance
        """
        # Update username if provided
        if "username" in data:
            new_username = data["username"].strip()

            if new_username != user.username:
                # Validate username
                if not re.match(r"^[a-zA-Z0-9_]+$", new_username):
                    raise ValidationError(
                        "Username can only contain letters, numbers, and underscores"
                    )

                if len(new_username) < 3 or len(new_username) > 30:
                    raise ValidationError(
                        "Username must be between 3 and 30 characters"
                    )

                # Check if username is taken
                if (
                    User.objects.filter(username=new_username)
                    .exclude(id=user.id)
                    .exists()
                ):
                    raise ValidationError("Username already taken")

                user.username = new_username

        # Update basic fields
        updateable_fields = ["first_name", "last_name", "bio", "birth_date", "country"]
        for field in updateable_fields:
            if field in data:
                setattr(user, field, data[field])

        # TODO: Handle profile_image upload
        # This would involve processing base64 or URL and saving to storage

        user.save()
        return user

    @staticmethod
    def update_preferences(user, data: Dict):
        """
        Update user preferences

        Args:
            user: User instance
            data: Dictionary with preferences data

        Returns:
            Updated UserPreferences instance
        """
        preferences, _ = UserPreferences.objects.get_or_create(user=user)

        # Validate audio quality
        if "audio_quality" in data:
            valid_qualities = ["low", "normal", "high"]
            if data["audio_quality"] not in valid_qualities:
                raise ValidationError(
                    f"Invalid audio quality. Must be one of: {', '.join(valid_qualities)}"
                )

        # Update fields
        updateable_fields = [
            "explicit_content",
            "autoplay",
            "audio_quality",
            "language",
            "private_session",
        ]
        for field in updateable_fields:
            if field in data:
                setattr(preferences, field, data[field])

        preferences.save()
        return preferences

    @staticmethod
    def delete_account(user, password: str):
        """
        Delete user account

        Args:
            user: User instance
            password: Password confirmation
        """
        if not password:
            raise ValidationError("Password is required to delete account")

        # Verify password
        if not user.check_password(password):
            raise ValidationError("Incorrect password")

        # In production, you might want to:
        # 1. Soft delete (set is_active=False)
        # 2. Anonymize data
        # 3. Keep some records for legal reasons

        with transaction.atomic():
            # Delete related data
            user.playlists.all().delete()
            user.liked_songs.all().delete()
            user.followed_artists.all().delete()

            # Delete user
            user.delete()

    @staticmethod
    def get_user_stats(user) -> Dict:
        """
        Get user statistics

        Args:
            user: User instance

        Returns:
            Dictionary with user statistics
        """
        from apps.playlists.models import Playlist
        from apps.interactions.models import LikedSong, FollowedArtist, ListeningHistory

        return {
            "playlists_count": Playlist.objects.filter(user=user).count(),
            "public_playlists_count": Playlist.objects.filter(
                user=user, is_public=True
            ).count(),
            "liked_songs_count": LikedSong.objects.filter(user=user).count(),
            "followed_artists_count": FollowedArtist.objects.filter(user=user).count(),
            "total_listening_time": UserService._calculate_listening_time(user),
            "subscription_type": user.subscription_type,
            "is_premium": user.subscription_type in ["premium", "family", "student"],
        }

    @staticmethod
    def _calculate_listening_time(user) -> int:
        """Calculate total listening time in seconds"""
        from apps.interactions.models import ListeningHistory
        from django.db.models import Sum

        total = ListeningHistory.objects.filter(user=user).aggregate(
            total_time=Sum("duration_played")
        )["total_time"]

        return total or 0
