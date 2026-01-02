import graphene


class RegisterInput(graphene.InputObjectType):
    """Input for user registration"""

    email = graphene.String(required=True)
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    birth_date = graphene.Date()
    gender = graphene.String()
    country = graphene.String()


class LoginInput(graphene.InputObjectType):
    """Input for user login"""

    email = graphene.String(required=True)
    password = graphene.String(required=True)


class UpdateProfileInput(graphene.InputObjectType):
    """Input for updating user profile"""

    first_name = graphene.String()
    last_name = graphene.String()
    bio = graphene.String()
    profile_image = graphene.String()
    birth_date = graphene.Date()
    gender = graphene.String()
    country = graphene.String()


class UpdatePreferencesInput(graphene.InputObjectType):
    """Input for updating user preferences"""

    explicit_content = graphene.Boolean()
    autoplay = graphene.Boolean()
    audio_quality = graphene.String()  # low, normal, high
    language = graphene.String()
    private_session = graphene.Boolean()


class ChangePasswordInput(graphene.InputObjectType):
    """Input for changing password"""

    old_password = graphene.String(required=True)
    new_password = graphene.String(required=True)
