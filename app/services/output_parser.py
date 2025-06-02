import logging
import re
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ParsedTagResponse(BaseModel):
    primary_tag: Optional[str] = None
    secondary_tags: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: Optional[str] = None
    is_valid: bool = True
    error: Optional[str] = None

class OutputParser:
    """
    Service for parsing LLM outputs
    """
    
    def __init__(self, available_tags: List[str] = None):
        self.available_tags = available_tags or []
        logger.info(f"OutputParser initialized with {len(self.available_tags)} available tags")
    
    async def parse_tag_response(
        self, 
        llm_output: str, 
        available_tags: List[str] = None
    ) -> ParsedTagResponse:
        """
        Parse LLM response into structured format
        TODO Task 4: Implement parsing logic
        """
        try:
            tags_to_use = available_tags or self.available_tags
            text = llm_output.strip()
            
            # Basic parsing
            primary_tag = self._extract_primary_tag(text, tags_to_use)
            confidence = self._extract_confidence(text)
            reasoning = self._extract_reasoning(text)
            
            if not primary_tag:
                return ParsedTagResponse(
                    is_valid=False,
                    error="No valid primary tag found in response"
                )
            
            return ParsedTagResponse(
                primary_tag=primary_tag,
                confidence=confidence,
                reasoning=reasoning,
                is_valid=True
            )
            
        except Exception as e:
            return ParsedTagResponse(
                is_valid=False,
                error=f"Parsing error: {str(e)}"
            )
    
    def _extract_primary_tag(self, text: str, available_tags: List[str]) -> Optional[str]:
        """Extract primary tag from text"""
        # Look for PRIMARY_TAG: pattern
        match = re.search(r'PRIMARY_TAG:\s*([A-Z_]+)', text, re.IGNORECASE)
        if match:
            tag = match.group(1).upper()
            if tag in available_tags:
                return tag
        
        # Fallback: find any mentioned tag
        text_upper = text.upper()
        for tag in available_tags:
            if tag in text_upper:
                return tag
        
        return None
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text"""
        match = re.search(r'CONFIDENCE:\s*([\d.]+)', text, re.IGNORECASE)
        if match:
            try:
                confidence = float(match.group(1))
                return max(0.0, min(1.0, confidence))
            except ValueError:
                pass
        return 0.5  # Default confidence
    
    def _extract_reasoning(self, text: str) -> Optional[str]:
        """Extract reasoning from text"""
        match = re.search(r'REASONING:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None