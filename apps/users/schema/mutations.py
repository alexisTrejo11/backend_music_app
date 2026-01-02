from typing import Dict
import graphene
from .types import *
from .inputs import *
from ..services import AuthService, UserService
from apps.core.base_schema import BaseMutation


class AuthMutation(BaseMutation):
    """Base class for authentication mutations"""

    auth_payload = graphene.Field(AuthPayloadType)

    class Meta:
        abstract = True


class Register(AuthMutation):
    """Register a new user"""

    class Arguments:
        input = RegisterInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        result = cls.execute_service_method(AuthService.register_user, input)

        if isinstance(result, BaseMutation):
            return result

        auth_payload = cls.create_auth_payload(result)
        return cls.success_response(
            message="Registration successful", auth_payload=auth_payload
        )


class Login(AuthMutation):
    """Login user"""

    class Arguments:
        input = LoginInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        email = input.get("email", "").strip()
        password = input.get("password", "")

        result = cls.execute_service_method(AuthService.login_user, email, password)

        if isinstance(result, BaseMutation):
            return result

        auth_payload = cls.create_auth_payload(result)
        return cls.success_response(
            message="Login successful", auth_payload=auth_payload
        )


class RefreshToken(AuthMutation):
    """Refresh JWT token"""

    class Arguments:
        refresh_token = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, refresh_token: str):
        result = cls.execute_service_method(
            AuthService.refresh_access_token, refresh_token
        )

        if isinstance(result, BaseMutation):
            return result

        auth_payload = cls.create_auth_payload(result)
        return cls.success_response(
            message="Token refreshed successfully", auth_payload=auth_payload
        )


class UpdateProfile(BaseMutation):
    """Update user profile"""

    class Arguments:
        input = UpdateProfileInput(required=True)

    user = graphene.Field(UserType)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        user = cls.require_authentication(info)

        result = cls.execute_service_method(UserService.update_profile, user, input)

        if isinstance(result, BaseMutation):
            return result

        return cls.success_response(message="Profile updated successfully", user=result)


class UpdatePreferences(BaseMutation):
    """Update user preferences"""

    class Arguments:
        input = UpdatePreferencesInput(required=True)

    preferences = graphene.Field(UserPreferencesType)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        user = cls.require_authentication(info)

        result = cls.execute_service_method(UserService.update_preferences, user, input)

        if isinstance(result, BaseMutation):
            return result

        return cls.success_response(
            message="Preferences updated successfully", preferences=result
        )


class ChangePassword(BaseMutation):
    """Change user password"""

    class Arguments:
        input = ChangePasswordInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        user = cls.require_authentication(info)

        result = cls.execute_service_method(
            AuthService.change_password,
            user,
            input.get("old_password"),
            input.get("new_password"),
        )

        if isinstance(result, BaseMutation):
            return result

        return cls.success_response(message="Password changed successfully")


class DeleteAccount(BaseMutation):
    """Delete user account"""

    class Arguments:
        password = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, password: str):
        user = cls.require_authentication(info)

        result = cls.execute_service_method(UserService.delete_account, user, password)

        if isinstance(result, BaseMutation):
            return result

        return cls.success_response(message="Account deleted successfully")
