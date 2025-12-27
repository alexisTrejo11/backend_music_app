import graphene
import apps.artists.schema as artists_schema


# TODO: Fix Type Error
class Query(artists_schema.ArtistQuery, graphene.ObjectType):
    # This will inherit queries from all apps
    pass


class Mutation(artists_schema.ArtistMutation, graphene.ObjectType):
    # This will inherit mutations from all apps
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
