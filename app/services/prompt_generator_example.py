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
        """
        
        # Build available categories for the prompt
        categories_text = []
        for tag_key, tag_info in self.available_tags.items():
            display_name = tag_info.get('display_name', tag_key)
            description = tag_info.get('description', '')
            tag_navn = tag_info.get('underkategori', '').upper()
            #examples = tag_info.get('examples', [])
            
            category_desc = f"Tag navn:{tag_navn}. Beskrivelse af tag: {description}"
            #if examples:
            #    category_desc += f" (Eksempler: {', '.join(examples[:3])})"
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
        
        categories_text_str = "\n".join(categories_text)

        prompt = f"""
Du er en ekspert i at tagge danske arrangementer og events.

Arrangement der skal tagges:
Titel: {arrangement.arrangement_titel}
Arrangør: {arrangement.arrangør or 'Ikke angivet'}
Type: {arrangement.arrangement_undertype or 'Ikke angivet'}
{description_text}

Tilgængelige tags:
{categories_text_str}

Bestem de mest passende tags for dette arrangement. Minimum 1 tag og maximum 3 tags.

Tags always use _ instead of whitespace.

Svade udelukkende i følgende format, og output empty string hvis ingen tags for tag2 og tag3:

{{
  "TAG1": "navn_på_tag1",
  "TAG2": "navn_på_tag2",
  "TAG3": "navn_på_tag3"
  "CONFIDENCE": x,
  "REASONING": "reason"
}}

Eksempel:

Input: Du er en ekspert i at tagge danske arrangementer og events.

Arrangement der skal tagges:
Titel: "Arrangement A"
Arrangør: Arrangør X
Type: Y
Dette arrangement er et eksempel arrangement.

Tilgængelige tags:
kategori x
kategori y
kategori

Bestem de mest passende tags for dette arrangement. Minimum 1 tag og maximum 3 tags.

Tags always use _ instead of whitespace.

Svade udelukkende i følgende format, og output empty string hvis ingen tags for tag2 og tag3:

{{
  "TAG1": "navn_på_tag1",
  "TAG2": "navn_på_tag2",
  "TAG3": "navn_på_tag3"
  "CONFIDENCE": x,
  "REASONING": "reason"
}}

Output:
{{
  "TAG1": "navn_på_tag1",
  "TAG2": "navn_på_tag2",
  "TAG3": ""
  "CONFIDENCE": x,
  "REASONING": "reason"
}}
        """
        
        return PromptResponse(
            prompt=prompt.strip(),
            available_tags=list(self.available_tags.keys())
        )