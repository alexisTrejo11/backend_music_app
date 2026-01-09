import graphene
import logging
from apps.core.base_schema import BaseMutation
from apps.core.decorators import auth_required, get_authenticated_user
from apps.interactions.services.interaction_service import InteractionService
from ..inputs import TrackPlayInput


logger = logging.getLogger(__name__)


class TrackPlay(BaseMutation):
    """Track a song play in listening history"""

    class Arguments:
        input = TrackPlayInput(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        song_id = input.get("song_id")
        completed = input.get("completed", False)
        logger.debug(
            f"User {user.id} tracking play for song {song_id} (completed: {completed})"
        )

        try:
            InteractionService.track_play(
                user,
                input.get("song_id"),
                input.get("duration_played"),
                input.get("completed", False),
                input.get("source"),
                input.get("source_id"),
            )
            logger.info(
                f"Play tracked successfully for song {song_id} by user {user.id}"
            )
            return TrackPlay.success_response(message="Play tracked successfully")
        except Exception as e:
            logger.error(
                f"Failed to track play for song {song_id} by user {user.id}: {str(e)}"
            )
            return TrackPlay.failure_response(message=str(e))


class ClearListeningHistory(BaseMutation):
    """Clear user's listening history"""

    class Arguments:
        confirm = graphene.Boolean(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @auth_required
    def mutate(cls, root, info, confirm):
        if not confirm:
            logger.warning("Clear listening history attempted without confirmation")
            return ClearListeningHistory(success=False, message="Confirmation required")

        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to clear listening history")

        try:
            InteractionService.clear_listening_history(user)
            logger.info(f"Listening history cleared successfully for user {user.id}")
            return ClearListeningHistory.success_response(
                message="Listening history cleared successfully"
            )
        except Exception as e:
            logger.error(
                f"Failed to clear listening history for user {user.id}: {str(e)}"
            )
            return ClearListeningHistory.failure_response(message=str(e))
