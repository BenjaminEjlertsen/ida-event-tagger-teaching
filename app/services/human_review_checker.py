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
        TODO Task 6: Implement review logic
        """
        # Basic implementation
        if confidence_scores.primary_confidence < self.review_threshold:
            return ReviewCheckResult(
                needs_review=True,
                reason=f"Low confidence: {confidence_scores.primary_confidence:.2f}"
            )
        
        if not parsed_tags.is_valid:
            return ReviewCheckResult(
                needs_review=True,
                reason="Invalid AI response"
            )
        
        return ReviewCheckResult(needs_review=False)