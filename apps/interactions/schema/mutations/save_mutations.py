import graphene
import logging
from graphql import GraphQLError
from apps.core.decorators import auth_required, get_authenticated_user
from apps.core.base_schema import BaseMutation
from apps.interactions.services.interaction_service import InteractionService

logger = logging.getLogger(__name__)


class SaveAlbum(BaseMutation):
    """Save an album to user's library"""

    class Arguments:
        album_id = graphene.ID(required=True)

    album = graphene.Field("apps.music.schema.AlbumType")

    @classmethod
    @auth_required
    def mutate(cls, root, info, album_id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to save album {album_id}")

        try:
            album = InteractionService.save_album(user, album_id)
            logger.info(f"Album {album_id} saved successfully by user {user.id}")
            return SaveAlbum.success_response(
                message="Album saved successfully",
                album=album,
            )
        except Exception as e:
            logger.error(
                f"Failed to save album {album_id} for user {user.id}: {str(e)}"
            )
            return SaveAlbum.failure_response(message=str(e))


class UnsaveAlbum(BaseMutation):
    """Remove an album from user's library"""

    class Arguments:
        album_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @auth_required
    def mutate(cls, root, info, album_id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to unsave album {album_id}")

        try:
            result = InteractionService.unsave_album(user, album_id)
            if not result["success"]:
                logger.warning(
                    f"Failed to unsave album {album_id} for user {user.id}: {result['message']}"
                )
                return UnsaveAlbum.failure_response(message=result["message"])

            logger.info(f"Album {album_id} unsaved successfully by user {user.id}")
            return UnsaveAlbum.success_response(message=result["message"])
        except Exception as e:
            logger.error(
                f"Error unsaving album {album_id} for user {user.id}: {str(e)}"
            )
            return UnsaveAlbum.failure_response(message=str(e))
