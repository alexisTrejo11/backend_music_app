import graphene
import apps.artists.schema as artists_schema


class Query(artists_schema.Query, graphene.ObjectType):
    # This will inherit queries from all apps
    pass


class Mutation(artists_schema.Mutation, graphene.ObjectType):
    # This will inherit mutations from all apps
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
