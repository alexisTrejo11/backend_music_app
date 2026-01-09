import graphene
from .mutations import (
    SaveAlbum,
    UnsaveAlbum,
    AddReview,
    UpdateReview,
    DeleteReview,
    MarkReviewHelpful,
    ClearListeningHistory,
    TrackPlay,
)
from .queries import (
    LikesQueries,
    AnalyticsQueries,
    FollowQueries,
    ListeningHistoryQueries,
)


class Mutation(graphene.ObjectType):
    """Playlist-related GraphQL mutations"""

    track_play = TrackPlay.Field()
    save_album = SaveAlbum.Field()
    unsave_album = UnsaveAlbum.Field()
    add_review = AddReview.Field()
    update_review = UpdateReview.Field()
    delete_review = DeleteReview.Field()
    mark_review_helpful = MarkReviewHelpful.Field()
    clear_listening_history = ClearListeningHistory.Field()


class Query(LikesQueries, AnalyticsQueries, FollowQueries, ListeningHistoryQueries):
    """Combined GraphQL queries for interactions app"""

    pass
