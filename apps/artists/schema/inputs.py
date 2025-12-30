import graphene


class SocialLinksInput(graphene.InputObjectType):
    """Input for social media links"""

    website = graphene.String()
    spotify = graphene.String()
    instagram = graphene.String()
    twitter = graphene.String()


class CreateArtistInput(graphene.InputObjectType):
    """Input for creating an artist"""

    name = graphene.String(required=True)
    bio = graphene.String()
    profile_image = graphene.String()  # Base64 or URL
    cover_image = graphene.String()  # Base64 or URL
    genres = graphene.List(graphene.String)
    country = graphene.String()
    social_links = graphene.Field(SocialLinksInput)
