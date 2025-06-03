import time
from typing import Dict, Any
from ..models.requests import EventTagRequest
from ..config import settings

def calculate_processing_time(start_time: float) -> float:
    """Calculate processing time in milliseconds"""
    return (time.time() - start_time) * 1000

def estimate_cost(tokens_used: int) -> float:
    """Estimate cost based on token usage"""
    # TODO: Implement cost calculation based on OpenAI pricing
    cost_per_1k_tokens = 0.03  # Example rate for GPT-4
    return (tokens_used / 1000) * cost_per_1k_tokens

def format_event_for_processing(arrangement: EventTagRequest) -> str:
    """Format arrangement data for LLM processing"""
    # Build description from available fields
    description_parts = []
    
    if arrangement.nc_teaser:
        description_parts.append(f"Teaser: {arrangement.nc_teaser}")
    
    if arrangement.beskrivelse_html_fri:
        description_parts.append(f"Beskrivelse: {arrangement.beskrivelse_html_fri}")
    elif arrangement.nc_beskrivelse:
        description_parts.append(f"Beskrivelse: {arrangement.nc_beskrivelse}")
    
    description_text = "\n".join(description_parts) if description_parts else "Ingen beskrivelse tilgængelig"
    
    # Get organizer
    organizer = arrangement.arrangør or "Ikke angivet"
    
    return f"""
    Titel: {arrangement.arrangement_titel}
    Arrangør: {organizer}
    Type: {arrangement.arrangement_undertype or 'Ikke angivet'}
    {description_text}
    """