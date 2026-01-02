import graphene
from .queries import UserQueryMixin
from .mutations import (
    Register,
    Login,
    UpdateProfile,
    UpdatePreferences,
    ChangePassword,
    DeleteAccount,
)


class Query(UserQueryMixin, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    register_user = Register.Field()
    login_user = Login.Field()
    update_profile = UpdateProfile.Field()
    update_preferences = UpdatePreferences.Field()
    change_password = ChangePassword.Field()
    delete_user = DeleteAccount.Field()
