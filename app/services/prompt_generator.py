import logging
from typing import Dict, List
from pydantic import BaseModel

from ..models.requests import EventTagRequest

logger = logging.getLogger(__name__)

class PromptResponse(BaseModel):
    prompt: str
    available_tags: List[str]

class PromptGenerator:
    """
    Service for generating prompts for OpenAI
    """
    
    def __init__(self, available_tags: Dict = None, tag_rules: List = None):
        self.available_tags = available_tags or {}
        self.tag_rules = tag_rules or []
        logger.info(f"PromptGenerator initialized with {len(self.available_tags)} tags")
    
    async def generate_tagging_prompt(
        self, 
        arrangement: EventTagRequest
    ) -> PromptResponse:
        """
        Generate tagging prompt for event
        TODO Implement prompt generation logic
        """

        prompt = f"""
        Den perfekte prompt
        """
        
        return PromptResponse(
            prompt=prompt.strip(),
            available_tags=list(self.available_tags.keys())
        )