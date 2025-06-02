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
    Service for generating prompts for OpenAI - Danish version
    """
    
    def __init__(self, available_tags: Dict = None, tag_rules: List = None):
        self.available_tags = available_tags or {}
        self.tag_rules = tag_rules or []
        logger.info(f"PromptGenerator initialized with {len(self.available_tags)} Danish tags")
    
    async def generate_tagging_prompt(
        self, 
        arrangement: EventTagRequest, 
        custom_prompt: str = None
    ) -> PromptResponse:
        """
        Generate tagging prompt for a Danish arrangement
        TODO Task 2: Implement prompt generation logic
        """
        if custom_prompt:
            return PromptResponse(
                prompt=custom_prompt,
                available_tags=list(self.available_tags.keys())
            )
        
        # Build available categories for the prompt
        categories_text = []
        for tag_key, tag_info in self.available_tags.items():
            display_name = tag_info.get('display_name', tag_key)
            description = tag_info.get('description', '')
            examples = tag_info.get('examples', [])
            
            category_desc = f"- {display_name}: {description}"
            if examples:
                category_desc += f" (Eksempler: {', '.join(examples[:3])})"
            categories_text.append(category_desc)
        
        # Get the best description from available fields
        description_parts = []
        if arrangement.nc_teaser:
            description_parts.append(f"Teaser: {arrangement.nc_teaser}")
        if arrangement.beskrivelse_html_fri:
            description_parts.append(f"Beskrivelse: {arrangement.beskrivelse_html_fri}")
        elif arrangement.nc_beskrivelse:
            description_parts.append(f"Beskrivelse: {arrangement.nc_beskrivelse}")
        
        description_text = "\n".join(description_parts) if description_parts else "Ingen beskrivelse tilgængelig"
        
        # Danish prompt
        prompt = f"""
Du er en ekspert i at kategorisere danske arrangementer og events.

Arrangement der skal kategoriseres:
Titel: {arrangement.arrangement_titel}
Arrangør: {arrangement.arrangør or 'Ikke angivet'}
Type: {arrangement.arrangement_undertype or 'Ikke angivet'}
{description_text}

Tilgængelige kategorier:
{chr(10).join(categories_text)}

Bestem den mest passende kategori for dette arrangement.

Svar med følgende format:
PRIMARY_TAG: [kategori_navn]
CONFIDENCE: [score fra 0.0 til 1.0]
REASONING: [kort forklaring på dansk]
        """
        
        return PromptResponse(
            prompt=prompt.strip(),
            available_tags=list(self.available_tags.keys())
        )