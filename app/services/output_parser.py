import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

class ParsedTagResponse(BaseModel):
    tag1: Optional[str] = None
    tag2: Optional[str] = None
    tag3: Optional[str] = None

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
        TODO Parse LLM response into structured format that supports the ParsedTagReponse

        OBS: Systemet forventer takes i all caps og _
        Fx skal "Programmering og softwareudvkling" outputtes som "PROGRAMMERING_OG_SOFTWAREUDVIKLING"
        """
        try:
            tags_to_use = available_tags or self.available_tags
            
            tag1 = "PROGRAMMERING_OG_SOFTWAREUDVIKLING"
            tag2 = ""
            tag3 = ""
            confidence = -1
            reasoning = "Bare fordi"

            return ParsedTagResponse(
                tag1=tag1.upper() if tag1 else None,
                tag2=tag2.upper() if tag2 else None,
                tag3=tag3.upper() if tag3 else None,
                confidence=confidence or 0.0,
                reasoning=reasoning,
                is_valid=True
            )

        except json.JSONDecodeError as e:
            return ParsedTagResponse(
                is_valid=False,
                error=f"Could not parse JSON: {str(e)}"
            )
