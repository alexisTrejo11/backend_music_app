import graphene
import logging
from apps.core.decorators import auth_required, get_authenticated_user
from apps.core.base_schema import BaseMutation
from apps.interactions.services.interaction_service import InteractionService

logger = logging.getLogger(__name__)


class ClearListeningHistory(BaseMutation):
    """Clear user's listening history"""

    class Arguments:
        confirm = graphene.Boolean(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, confirm):
        user = get_authenticated_user(info)

        logger.info(f"User {user.id} requested to clear listening history.")

        if not confirm:
            return ClearListeningHistory.failure_response(
                message="Confirmation required"
            )

        try:
            logger.info(f"Clearing listening history for user {user.id}.")
            InteractionService.clear_listening_history(user)

            logger.info(f"Listening history cleared for user {user.id}.")
            return ClearListeningHistory.success_response(
                message="Listening history cleared successfully"
            )
        except Exception as e:
            return ClearListeningHistory.failure_response(message=str(e))
