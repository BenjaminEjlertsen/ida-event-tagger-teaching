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
    Service for validating and cleaning Danish arrangement data
    """
    
    def __init__(self):
        self.sensitive_keywords = [
            # Danish sensitive keywords
            "klassificeret", "hemmeligt", "fortroligt", "privat", 
            "personfølsomme", "gdpr", "databeskyttelse"
        ]
    
    async def validate_and_clean(self, arrangement: EventTagRequest) -> EventTagRequest:
        """
        Validate and clean Danish arrangement data
        TODO Task 1: Implement validation logic
        """
        logger.info(f"Validating arrangement: {arrangement.arrangement_titel[:50]}...")
        
        # Check required fields
        if not arrangement.arrangement_titel or len(arrangement.arrangement_titel.strip()) < 3:
            raise ValueError("ArrangementTitel skal være mindst 3 tegn")
        
        # Check if we have some description
        has_description = any([
            arrangement.nc_teaser,
            arrangement.nc_beskrivelse,
            arrangement.beskrivelse_html_fri
        ])
        
        if not has_description:
            logger.warning(f"No description available for arrangement: {arrangement.arrangement_titel}")
        
        cleaned_arrangement = arrangement.copy()
        
        # Clean text fields
        if cleaned_arrangement.arrangement_titel:
            cleaned_arrangement.arrangement_titel = self._clean_text(cleaned_arrangement.arrangement_titel)
        if cleaned_arrangement.nc_teaser:
            cleaned_arrangement.nc_teaser = self._clean_text(cleaned_arrangement.nc_teaser)
        if cleaned_arrangement.nc_beskrivelse:
            cleaned_arrangement.nc_beskrivelse = self._clean_text(cleaned_arrangement.nc_beskrivelse)
        if cleaned_arrangement.beskrivelse_html_fri:
            cleaned_arrangement.beskrivelse_html_fri = self._clean_text(cleaned_arrangement.beskrivelse_html_fri)
        
        return cleaned_arrangement
    
    async def check_sensitive_content(self, arrangement: EventTagRequest) -> SensitivityCheckResult:
        """
        Check if arrangement contains sensitive content
        TODO Task 1: Implement sensitivity detection
        """
        # Combine all text fields for checking
        text_to_check = " ".join([
            arrangement.arrangement_titel or "",
            arrangement.nc_teaser or "",
            arrangement.nc_beskrivelse or "",
            arrangement.beskrivelse_html_fri or ""
        ]).lower()
        
        for keyword in self.sensitive_keywords:
            if keyword.lower() in text_to_check:
                return SensitivityCheckResult(
                    contains_sensitive_content=True,
                    reason=f"Indeholder følsomt nøgleord: {keyword}",
                    confidence=0.8
                )
        
        return SensitivityCheckResult(contains_sensitive_content=False)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize Danish text"""
        if not text:
            return text
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text