import time
from typing import Dict, Any
from ..models.requests import EventTagRequest
from ..config import settings
import re

def calculate_processing_time(start_time: float) -> float:
    """Calculate processing time in milliseconds"""
    return (time.time() - start_time) * 1000

def usd_to_dkk(cost_usd: float, rate: float = 6.5721) -> float:
    """
    Convert a USD amount into DKK using the given USD→DKK rate.
    Default rate is 6.5721 DKK per USD (as of 1 June 2025).
    """
    return round(cost_usd * rate, 4)

def estimate_cost(total_tokens: int) -> float:
    """
    Estimate USD cost given the total number of tokens (input + output),
    for the model named in settings.openai_model. We only use total_tokens
    and do NOT differentiate input vs. output.

    Model-specific combined rates (USD per 1k total tokens), computed as:
      avg_rate_per_1k = ((input_price_1M + output_price_1M) / 2) / 1000
    """

    model = settings.openai_model.lower()

    if re.match(r"gpt-4\.1$", model):
        # Input $3.00, Output $12.00 per 1M → Combined ($3+12)/2000 = $0.00750/1k
        combined_rate = 0.00750
    elif re.match(r"gpt-4\.1-mini$", model):
        # Input $0.80, Output $3.20 per 1M → Combined ($0.8+3.2)/2000 = $0.00200/1k
        combined_rate = 0.00200
    elif re.match(r"o1-?preview$", model) or re.match(r"o1$", model):
        # o1-Preview: Input $15, Output $60 per 1M → Combined ($15+60)/2000 = $0.03750/1k
        combined_rate = 0.03750
    elif re.match(r"o1-?mini$", model):
        # o1-Mini: Input $3, Output $12 per 1M → Combined ($3+12)/2000 = $0.00750/1k
        combined_rate = 0.00750
    elif re.match(r"gpt-4o", model) or re.match(r"gpt-4o$", model):
        # GPT-4o (2024-08-06): Input $2.50, Output $10 per 1M → Combined ($2.5+10)/2000 = $0.00625/1k
        combined_rate = 0.00625 
    elif re.match(r"gpt-4o-mini$", model):
        # GPT-4o-Mini: Input $0.15, Output $0.60 per 1M → Combined ($0.15+0.6)/2000 = $0.000375/1k
        combined_rate = 0.000375
    elif re.match(r"o3$", model):
        # o3: Input $10, Output $40 per 1M → Combined ($10+40)/2000 = $0.02500/1k
        combined_rate = 0.02500
    elif re.match(r"o4-?mini$", model):
        # o4-Mini: Input $1.10, Output $4.40 per 1M → Combined ($1.1+4.4)/2000 = $0.00275/1k
        combined_rate = 0.00275
    else:
        raise ValueError(
            f"Model '{settings.openai_model}' not recognized. "
            "Supported: GPT-4.1, GPT-4.1-mini, o1-preview, o1-mini, GPT-4o, GPT-4o-mini, o3, o4-mini."
        )

    # Compute cost using total_tokens and combined rate (USD per 1k tokens)
    cost_usd = (total_tokens / 1000) * combined_rate
    return round(usd_to_dkk(cost_usd), 8)


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