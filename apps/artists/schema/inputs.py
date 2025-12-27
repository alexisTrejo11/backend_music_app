import graphene


class ArtistInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    bio = graphene.String()
    image = graphene.String()


class ArtistUpdateInput(graphene.InputObjectType):
    artist_id = graphene.Int(required=True)
    name = graphene.String()
    bio = graphene.String()
    image = graphene.String()


class ArtistDeleteInput(graphene.InputObjectType):
    artist_id = graphene.Int(required=True)
