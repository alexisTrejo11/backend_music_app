import graphene
import logging
from apps.core.base_schema import BaseMutation
from apps.core.decorators import auth_required, get_authenticated_user
from apps.interactions.services.interaction_service import InteractionService
from ..types import ReviewType
from ..inputs import AddReviewInput, UpdateReviewInput

logger = logging.getLogger(__name__)


class AddReview(BaseMutation):
    """Add a review for an album or song"""

    class Arguments:
        input = AddReviewInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    review = graphene.Field(ReviewType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to add review for {input.get('content_type')} ID {input.get('content_id')}"
        )

        try:
            review = InteractionService.add_review(user, input)
            logger.info(
                f"Review added successfully by user {user.id} with rating {input.get('rating')}"
            )
            return AddReview.success_response(
                message="Review added successfully", review=review
            )
        except Exception as e:
            logger.error(f"Failed to add review for user {user.id}: {str(e)}")
            return AddReview.failure_response(message=str(e))


class UpdateReview(BaseMutation):
    """Update an existing review"""

    class Arguments:
        review_id = graphene.ID(required=True)
        input = UpdateReviewInput(required=True)

    review = graphene.Field(ReviewType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, review_id, input):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to update review {review_id}")

        try:
            review = InteractionService.update_review(user, review_id, input)
            logger.info(f"Review {review_id} updated successfully by user {user.id}")
            return UpdateReview.success_response(
                message="Review updated successfully", review=review
            )
        except Exception as e:
            logger.error(
                f"Failed to update review {review_id} for user {user.id}: {str(e)}"
            )
            return UpdateReview.failure_response(message=str(e))


class DeleteReview(BaseMutation):
    """Delete a review"""

    class Arguments:
        review_id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, review_id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to delete review {review_id}")
        logger.info(f"User {user.id} attempting to delete review {review_id}")

        try:
            InteractionService.delete_review(user, review_id)
            logger.info(f"Review {review_id} deleted successfully by user {user.id}")
            return DeleteReview.success_response(message="Review deleted successfully")
        except Exception as e:
            logger.error(
                f"Failed to delete review {review_id} for user {user.id}: {str(e)}"
            )
            return DeleteReview.failure_response(message=str(e))


class MarkReviewHelpful(BaseMutation):
    """Mark a review as helpful"""

    class Arguments:
        review_id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, review_id):
        user = get_authenticated_user(info)
        logger.debug(f"User {user.id} marking review {review_id} as helpful")

        try:
            InteractionService.mark_review_helpful(user, review_id)
            logger.info(f"Review {review_id} marked as helpful by user {user.id}")
            return MarkReviewHelpful(success=True, message="Review marked as helpful")
        except Exception as e:
            logger.error(
                f"Failed to mark review {review_id} as helpful for user {user.id}: {str(e)}"
            )
            return MarkReviewHelpful(success=False, message=str(e))
