import graphene
from typing import Any, Dict
from django.core.exceptions import PermissionDenied, ValidationError


class TypedBaseMutation(graphene.Mutation):
    """Base mutation with typed response"""

    success = graphene.Boolean(required=True)
    message = graphene.String()

    class Meta:
        abstract = True

    @classmethod
    def create_response(cls, success: bool, message: str = "", data: Any = None):
        return cls(
            success=success,
            message=message,
            **({"data": data} if data is not None else {})
        )  # pyright: ignore[reportCallIssue]

    @classmethod
    def error_response(cls, message: str = ""):
        return cls.create_response(success=False, message=message, data=None)

    @classmethod
    def success_response(cls, data: Any = None, message: str = ""):
        return cls.create_response(success=True, message=message, data=data)


class BaseMutation(graphene.Mutation):
    """Base mutation with common functionality"""

    success = graphene.Boolean(required=True)
    message = graphene.String()

    class Meta:
        abstract = True

    @classmethod
    def require_authentication(cls, info) -> Any:
        """Ensure user is authenticated"""
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")
        return user

    @classmethod
    def execute_service_method(cls, service_method, *args, **kwargs) -> Any:
        """Execute service method with error handling"""
        try:
            return service_method(*args, **kwargs)
        except ValidationError as e:
            return cls.error_response(message=str(e))

    @classmethod
    def create_auth_payload(cls, result: Dict):
        """Create authentication payload from service result"""
        from apps.users.schema.types import AuthPayloadType

        return AuthPayloadType(
            user=result.get("user"),
            access_token=result.get("access_token") or result.get("token"),
            refresh_token=result.get("refresh_token"),
        )

    @classmethod
    def error_response(cls, message: str = "") -> graphene.Mutation:
        """Create error response"""
        return cls(success=False, message=message)

    @classmethod
    def success_response(cls, message: str = "", **kwargs) -> graphene.Mutation:
        """Create success response with optional data"""
        return cls(success=True, message=message, **kwargs)
