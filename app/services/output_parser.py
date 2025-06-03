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
        Parse LLM response into structured format (tag1, tag2, tag3)
        """
        try:
            tags_to_use = available_tags or self.available_tags
            text = llm_output.strip()
            data = json.loads(text)  # Expect JSON with keys "TAG1", "TAG2", "TAG3", "CONFIDENCE", "REASONING"

            # Extract the three tags
            tag1 = data.get("TAG1")
            tag2 = data.get("TAG2")
            tag3 = data.get("TAG3")

            confidence = data.get("CONFIDENCE")
            reasoning = data.get("REASONING")

            # Validate that at least tag1 is nonempty and within available_tags (if you want to enforce that)
            if not tag1:
                return ParsedTagResponse(
                    is_valid=False,
                    error="No valid tag1 found in response"
                )

            # Optionally check that each tagX is one of the allowed tags_to_use:
            for idx, t in enumerate((tag1, tag2, tag3), start=1):
                if t and t.upper() not in tags_to_use:
                    return ParsedTagResponse(
                        is_valid=False,
                        error=f"TAG{idx} = '{t}' is not in available_tags"
                    )

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

    def _extract_primary_tag(self, text: str, available_tags: List[str]) -> Optional[str]:
        # (You can remove or ignore this helper if you no longer extract a single primary_tag.)
        match = re.search(r'TAG1:\s*([A-Z_]+)', text, re.IGNORECASE)
        if match:
            tag = match.group(1).upper()
            if tag in available_tags:
                return tag
        text_upper = text.upper()
        for tag in available_tags:
            if tag in text_upper:
                return tag
        return None

    def _extract_confidence(self, text: str) -> float:
        match = re.search(r'CONFIDENCE:\s*([\d.]+)', text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                return max(0.0, min(1.0, val))
            except ValueError:
                pass
        return 0.5  # default

    def _extract_reasoning(self, text: str) -> Optional[str]:
        match = re.search(r'REASONING:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
