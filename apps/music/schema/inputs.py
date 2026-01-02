import graphene


class CreateSongInput(graphene.InputObjectType):
    """Input for creating a song"""

    title = graphene.String(required=True)
    artist_id = graphene.ID(required=True)
    album_id = graphene.ID(required=True)
    featured_artist_ids = graphene.List(graphene.ID)
    audio_file = graphene.String()  # Base64 or file path
    duration = graphene.Int(required=True)  # in seconds
    track_number = graphene.Int(default_value=1)
    disc_number = graphene.Int(default_value=1)
    isrc = graphene.String()
    lyrics = graphene.String()
    is_explicit = graphene.Boolean(default_value=False)
    genre_id = graphene.ID()
    mood = graphene.String()
    language = graphene.String()


class UpdateSongInput(graphene.InputObjectType):
    """Input for updating a song"""

    title = graphene.String()
    featured_artist_ids = graphene.List(graphene.ID)
    lyrics = graphene.String()
    is_explicit = graphene.Boolean()
    genre_id = graphene.ID()
    mood = graphene.String()
    language = graphene.String()


class CreateAlbumInput(graphene.InputObjectType):
    """Input for creating an album"""

    title = graphene.String(required=True)
    artist_id = graphene.ID(required=True)
    album_type = graphene.String(required=True)  # album, single, ep, compilation
    release_date = graphene.Date(required=True)
    cover_image = graphene.String()  # Base64 or URL
    description = graphene.String()
    label = graphene.String()
    is_explicit = graphene.Boolean(default_value=False)
    copyright = graphene.String()
    upc = graphene.String()


class UpdateAlbumInput(graphene.InputObjectType):
    """Input for updating an album"""

    title = graphene.String()
    description = graphene.String()
    cover_image = graphene.String()
    label = graphene.String()
    is_explicit = graphene.Boolean()
