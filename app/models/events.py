from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class Event(BaseModel):
    """Core event model"""
    id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    date: Optional[datetime] = Field(None, description="Event date")
    location: Optional[str] = Field(None, description="Event location")
    sector: Optional[str] = Field(None, description="Development sector")
    budget_usd: Optional[float] = Field(None, description="Budget in USD")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)

class TagRule(BaseModel):
    """Tag definition and rules"""
    tag: str = Field(..., description="Tag name")
    description: str = Field(..., description="Tag description")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with tag")
    rules: str = Field(..., description="Rules for applying this tag")
    examples: List[str] = Field(default_factory=list, description="Example applications")

class TaggedEvent(Event):
    """Event with assigned tags"""
    primary_tag: Optional[str] = Field(None, description="Primary assigned tag")
    secondary_tags: List[str] = Field(default_factory=list, description="Secondary assigned tags")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Tag confidence scores")
    human_verified: bool = Field(False, description="Whether tags were human verified")
    reasoning: Optional[str] = Field(None, description="AI reasoning for tag assignment")