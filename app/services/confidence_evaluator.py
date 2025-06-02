import logging
from typing import Dict
from pydantic import BaseModel, Field

from ..models.requests import EventTagRequest
from .output_parser import ParsedTagResponse
from .llm_client import LLMResponse

logger = logging.getLogger(__name__)

class ConfidenceScores(BaseModel):
    primary_confidence: float
    secondary_confidences: Dict[str, float] = Field(default_factory=dict)
    overall_confidence: float

class ConfidenceEvaluator:
    """
    Service for evaluating confidence in tag assignments
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        logger.info(f"ConfidenceEvaluator initialized with threshold {confidence_threshold}")
    
    async def evaluate_confidence(
        self,
        event: EventTagRequest,
        parsed_tags: ParsedTagResponse,
        llm_response: LLMResponse
    ) -> ConfidenceScores:
        """
        Evaluate confidence in tag assignments
        TODO Task 5: Implement confidence evaluation
        """
        # Basic implementation - improve this
        base_confidence = parsed_tags.confidence
        
        # Simple adjustments
        if llm_response.finish_reason == "stop":
            base_confidence += 0.05
        
        if len(parsed_tags.reasoning or "") > 30:
            base_confidence += 0.05
        
        final_confidence = min(1.0, max(0.0, base_confidence))
        
        return ConfidenceScores(
            primary_confidence=final_confidence,
            secondary_confidences={},
            overall_confidence=final_confidence
        )