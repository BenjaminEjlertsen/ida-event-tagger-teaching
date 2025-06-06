import logging
from pydantic import BaseModel

from ..models.requests import EventTagRequest
from .output_parser import ParsedTagResponse
from .confidence_evaluator import ConfidenceScores

logger = logging.getLogger(__name__)

class ReviewCheckResult(BaseModel):
    needs_review: bool
    reason: str = ""

class HumanReviewChecker:
    """
    Service for determining if human review is needed
    """
    
    def __init__(self, review_threshold: float = 0.5):
        self.review_threshold = review_threshold
        logger.info(f"HumanReviewChecker initialized with threshold {review_threshold}")
    
    async def needs_review(
        self,
        confidence_scores: ConfidenceScores,
        parsed_tags: ParsedTagResponse,
        event: EventTagRequest
    ) -> ReviewCheckResult:
        """
        Determine if human review is needed
        TODO Implement logic that decided whether or not human review is needed
        """

        return ReviewCheckResult(needs_review=False)