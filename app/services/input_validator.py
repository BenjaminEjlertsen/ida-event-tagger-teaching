import logging
import re
from typing import Optional
from pydantic import BaseModel

from ..models.requests import EventTagRequest

logger = logging.getLogger(__name__)

class SensitivityCheckResult(BaseModel):
    contains_sensitive_content: bool
    reason: Optional[str] = None
    confidence: float = 0.0

class InputValidator:
    """
    Service for validating and cleaning arrangement data
    """
    
    def __init__(self):
        self.sensitive_keywords = []
    
    async def validate_and_clean(self, arrangement: EventTagRequest) -> EventTagRequest:
        """
        Validate and clean arrangement data
        TODO Implement validation and cleaning.
        """
        logger.info(f"Validating arrangement: {arrangement.arrangement_titel[:50]}...")
        
        """Validation and clean logic here"""
        cleaned_arrangement = arrangement
        
        return cleaned_arrangement
    
    async def check_sensitive_content(self, arrangement: EventTagRequest) -> SensitivityCheckResult:
        """
        Check if arrangement contains sensitive content
        TODO Implement sensitivity detection
        """

        sensitive = False

        if sensitive:
            return SensitivityCheckResult(
                        contains_sensitive_content=True,
                        reason=f"",
                        confidence=0
                    )
        
        else:
            return SensitivityCheckResult(contains_sensitive_content=False)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        
        return text