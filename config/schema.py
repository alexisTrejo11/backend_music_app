import graphene
import apps.artists.schema as artists_schema
import apps.music.schema as music_schema
import apps.users.schema as users_schema
import apps.playlists.schema as playlists_schema
import apps.interactions.schema as interactions_schema


class Query(
    artists_schema.Query,
    music_schema.Query,
    users_schema.Query,
    playlists_schema.Query,
    interactions_schema.Query,
    graphene.ObjectType,
):
    # This will inherit queries from all apps
    pass


class Mutation(
    artists_schema.Mutation,
    music_schema.Mutation,
    users_schema.Mutation,
    playlists_schema.Mutation,
    interactions_schema.Mutation,
    graphene.ObjectType,
):
    # This will inherit mutations from all apps
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
