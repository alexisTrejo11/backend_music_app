import graphene
from typing import Any


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
