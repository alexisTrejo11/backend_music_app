import graphene


class SocialLinksInput(graphene.InputObjectType):
    """Input for social media links"""

    website = graphene.String()
    spotify = graphene.String()
    instagram = graphene.String()
    twitter = graphene.String()


class BaseArtistInput(graphene.InputObjectType):
    profile_image = graphene.String()
    cover_image = graphene.String()
    genres = graphene.List(graphene.String)
    country = graphene.String()
    verified = graphene.Boolean()
    social_links = graphene.Field(SocialLinksInput)


class CreateArtistInput(BaseArtistInput):
    """Input for creating an artist"""

    name = graphene.String(required=True)
    bio = graphene.String()


class UpdateArtistInput(BaseArtistInput):
    """Input for updating an artist"""

    name = graphene.String()
    verified = graphene.Boolean()


class AddArtistMemberInput(graphene.InputObjectType):
    """Input for adding an artist member"""

    artist_id = graphene.ID(required=True)
    name = graphene.String(required=True)
    role = graphene.String(required=True)
    image = graphene.String()
    join_date = graphene.Date()
