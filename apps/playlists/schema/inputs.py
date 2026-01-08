import graphene


class CreatePlaylistInput(graphene.InputObjectType):
    """Input for creating a playlist"""

    name = graphene.String(required=True)
    description = graphene.String()
    cover_image = graphene.String()  # Base64 or URL
    is_public = graphene.Boolean(default_value=True)
    is_collaborative = graphene.Boolean(default_value=False)


class UpdatePlaylistInput(graphene.InputObjectType):
    """Input for updating a playlist"""

    name = graphene.String()
    description = graphene.String()
    cover_image = graphene.String()
    is_public = graphene.Boolean()
    is_collaborative = graphene.Boolean()


class AddSongToPlaylistInput(graphene.InputObjectType):
    """Input for adding a song to a playlist"""

    playlist_id = graphene.ID(required=True)
    song_id = graphene.ID(required=True)
    position = graphene.Int()  # Optional, will append if not provided


class ReorderPlaylistSongsInput(graphene.InputObjectType):
    """Input for reordering songs in a playlist"""

    playlist_id = graphene.ID(required=True)
    song_id = graphene.ID(required=True)
    new_position = graphene.Int(required=True)
