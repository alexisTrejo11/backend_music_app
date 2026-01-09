import graphene


class AddReviewInput(graphene.InputObjectType):
    """Input for adding a review"""

    album_id = graphene.ID()
    song_id = graphene.ID()
    rating = graphene.Int(required=True)  # 1-5
    comment = graphene.String()


class UpdateReviewInput(graphene.InputObjectType):
    """Input for updating a review"""

    rating = graphene.Int()
    comment = graphene.String()


class TrackPlayInput(graphene.InputObjectType):
    """Input for tracking a play"""

    song_id = graphene.ID(required=True)
    duration_played = graphene.Int(required=True)  # seconds
    completed = graphene.Boolean(default_value=False)
    source = graphene.String()  # playlist, album, radio, search
    source_id = graphene.String()
