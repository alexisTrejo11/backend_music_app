import graphene

from .save_mutations import SaveAlbum, UnsaveAlbum
from .review_mutations import AddReview, UpdateReview, DeleteReview, MarkReviewHelpful
from .history_mutations import ClearListeningHistory, TrackPlay


__all__ = [
    "SaveAlbum",
    "UnsaveAlbum",
    "AddReview",
    "UpdateReview",
    "DeleteReview",
    "MarkReviewHelpful",
    "ClearListeningHistory",
    "TrackPlay",
]
