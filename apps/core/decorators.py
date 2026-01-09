from functools import wraps
from django.core.exceptions import PermissionDenied


def auth_required(func):
    """
    Decorator to require authentication for GraphQL mutations.
    Works with both regular methods and classmethods.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # For classmethods: args = (cls, root, info, ...)
        # For regular methods: args = (self, info, ...)
        # GraphQL mutations typically use classmethods, so info is at index 2
        if len(args) >= 3:
            info = args[2]  # classmethod: (cls, root, info, ...)
        elif len(args) >= 2:
            info = args[1]  # regular method: (self, info, ...)
        else:
            raise ValueError("Invalid arguments for auth_required decorator")

        if not hasattr(info, "context") or not hasattr(info.context, "user"):
            raise PermissionDenied("Authentication context not available")

        if not info.context.user.is_authenticated:
            raise PermissionDenied("Authentication required")

        return func(*args, **kwargs)

    return wrapper


def get_authenticated_user(info):
    user = info.context.user
    if not user.is_authenticated:
        raise PermissionDenied("Authentication required")
    return user
