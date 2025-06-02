from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class TagConfidence(str, Enum):
    HIGH = "high"       # > 0.8
    MEDIUM = "medium"   # 0.5 - 0.8
    LOW = "low"         # < 0.5

class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"

class TagResult(BaseModel):
    """Single tag result"""
    tag: str = Field(..., description="Tag name")
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0, le=1)
    confidence_level: TagConfidence = Field(..., description="Confidence level")
    
    @classmethod
    def from_confidence(cls, tag: str, confidence: float):
        if confidence > 0.8:
            level = TagConfidence.HIGH
        elif confidence > 0.5:
            level = TagConfidence.MEDIUM
        else:
            level = TagConfidence.LOW
        
        return cls(tag=tag, confidence=confidence, confidence_level=level)

class EventTagResponse(BaseModel):
    """Response model for a single event tagging"""
    event_id: Optional[str] = Field(None, description="Event identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    
    # Tagging results
    primary_tag: Optional[TagResult] = Field(None, description="Primary tag assignment")
    secondary_tags: List[TagResult] = Field(default_factory=list, description="Secondary tag assignments")
    
    # Metadata
    reasoning: Optional[str] = Field(None, description="AI reasoning for tag assignment")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    tokens_used: Optional[int] = Field(None, description="OpenAI tokens consumed")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    needs_human_review: bool = Field(False, description="Whether this result needs human review")
    
    @property
    def all_tags(self) -> List[str]:
        """Get all assigned tags"""
        tags = []
        if self.primary_tag:
            tags.append(self.primary_tag.tag)
        tags.extend([tag.tag for tag in self.secondary_tags])
        return tags

class BatchTagResponse(BaseModel):
    """Response model for batch event tagging"""
    batch_id: str = Field(..., description="Unique batch identifier")
    status: ProcessingStatus = Field(..., description="Overall batch status")
    
    # Results
    results: List[EventTagResponse] = Field(default_factory=list, description="Individual event results")
    
    # Summary statistics
    total_events: int = Field(..., description="Total events processed")
    successful_events: int = Field(0, description="Successfully processed events")
    failed_events: int = Field(0, description="Failed events")
    
    # Performance metrics
    total_processing_time_ms: float = Field(..., description="Total processing time")
    average_confidence: Optional[float] = Field(None, description="Average confidence across all tags")
    total_cost_usd: Optional[float] = Field(None, description="Total estimated cost")
    total_tokens_used: Optional[int] = Field(None, description="Total tokens consumed")
    
    # Human review
    events_needing_review: int = Field(0, description="Events flagged for human review")
    review_reasons: List[str] = Field(default_factory=list, description="Reasons for human review")

class EvaluationResponse(BaseModel):
    """Response model for evaluation results"""
    accuracy: float = Field(..., description="Overall accuracy")
    precision: float = Field(..., description="Overall precision")
    recall: float = Field(..., description="Overall recall")
    f1_score: float = Field(..., description="F1 score")
    
    tag_performance: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, 
        description="Per-tag performance metrics"
    )
    
    confusion_matrix: Optional[Dict[str, Any]] = Field(None, description="Confusion matrix data")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")