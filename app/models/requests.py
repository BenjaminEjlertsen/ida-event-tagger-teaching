from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum

class ProcessingMode(str, Enum):
    SINGLE = "single"
    BATCH = "batch" 
    STREAM = "stream"

class EventTagRequest(BaseModel):
    """Request model for tagging an event - supports both Danish and ASCII field names"""
    arrangement_nummer: Optional[str] = Field(None, description="ArrangementNummer")
    arrangement_titel: str = Field(..., description="ArrangementTitel", min_length=1, max_length=500)
    
    # Support both ø and ASCII versions
    arrangør: Optional[str] = Field(None, description="Arrangør (organizer)")
    arrangor: Optional[str] = Field(None, description="Organizer (ASCII version)")  # ASCII fallback
    
    arrangement_undertype: Optional[str] = Field(None, description="ArrangementUndertype")
    nc_teaser: Optional[str] = Field(None, description="nc_Teaser")
    nc_beskrivelse: Optional[str] = Field(None, description="nc_Beskrivelse")
    beskrivelse_html_fri: Optional[str] = Field(None, description="BeskrivelseHTMLfri")
    
    # Processing options
    include_reasoning: bool = Field(True, description="Include reasoning in response")
    require_confidence: bool = Field(True, description="Include confidence scores")
    
    @field_validator('arrangement_titel')
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if v else v
    
    @model_validator(mode='after')
    def merge_organizer_fields(self):
        """Merge arrangør and arrangor fields"""
        if not self.arrangør and self.arrangor:
            self.arrangør = self.arrangor
        return self

class BatchTagRequest(BaseModel):
    """Request model for tagging multiple arrangements"""
    events: List[EventTagRequest] = Field(..., description="List of arrangements to tag", min_items=1, max_items=100)
    processing_mode: ProcessingMode = Field(ProcessingMode.BATCH, description="How to process the batch")
    include_summary: bool = Field(True, description="Include batch processing summary")
    
    @field_validator('events')
    @classmethod
    def validate_events_unique(cls, v):
        arrangement_numbers = [event.arrangement_nummer for event in v if event.arrangement_nummer]
        if len(arrangement_numbers) != len(set(arrangement_numbers)):
            raise ValueError('ArrangementNummer must be unique')
        return v

class EvaluationRequest(BaseModel):
    """Request model for evaluating tagging performance"""
    test_events: List[Dict[str, Any]] = Field(..., description="Arrangements with expected tags")
    evaluation_metrics: List[str] = Field(["accuracy", "precision", "recall"], description="Metrics to calculate")


class SendSubmissionRequest(BaseModel):
    name: str
    csv_path: Optional[str] = None
