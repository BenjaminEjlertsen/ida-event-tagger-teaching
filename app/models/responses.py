from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    HUMAN_REVIEW_REQUIRED = "human_review_required"

class TagTriple(BaseModel):
    tag1: str
    tag2: Optional[str] = None
    tag3: Optional[str] = None
    confidence: float
    reasoning: Optional[str] = None

class EventTagResponse(BaseModel):
    """Response model for single event tagging"""
    event_id: str
    status: ProcessingStatus
    tag_triple: Optional[TagTriple] = None
    reasoning: Optional[str] = None
    processing_time_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    cost_dkk: Optional[float] = None
    error_message: Optional[str] = None
    needs_human_review: bool = False
    timestamp: datetime = datetime.now()

class BatchTagSummary(BaseModel):
    """Summary statistics for batch processing"""
    total_events: int
    successful: int
    failed: int
    needs_human_review: int
    total_processing_time_ms: float
    average_confidence: float

class BatchTagResponse(BaseModel):
    """Response model for batch event tagging"""
    batch_id: str
    status: ProcessingStatus
    results: List[EventTagResponse]
    summary: BatchTagSummary
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()

class EvaluationMetrics(BaseModel):
    """Evaluation metrics for tagging performance"""
    accuracy_at_1: float            # Exact match with first ground truth tag
    accuracy_at_2: float            # Match with any of top 2 ground truth tags
    accuracy_at_3: float            # Match with any of top 3 ground truth tags
    weighted_accuracy: float        # Weighted by priority (1st=1.0, 2nd=0.5, 3rd=0.33)
    exact_match_at_2: float
    exact_match_at_3: float

    precision: float
    recall: float
    f1_score: float

    average_confidence: float
    total_predictions: int
    correct_predictions: int

class EvaluationResult(BaseModel):
    """Individual evaluation result"""
    arrangement_id: str
    arrangement_title: str
    predicted_tag1: Optional[str]
    predicted_tag2: Optional[str]
    predicted_tag3: Optional[str]
    predicted_confidence: float
    ground_truth_tags: List[str]    # Ordered by priority
    is_correct: bool
    match_priority: Optional[int] = None  # 1, 2, 3 if matched; else None
    error_message: Optional[str] = None

class EvaluationResponse(BaseModel):
    """Response model for evaluation"""
    evaluation_id: str
    metrics: EvaluationMetrics
    results: List[EvaluationResult]
    processing_time_ms: float
    timestamp: datetime

    # Additional insights
    most_confused_tags: Dict[str, int] = {}
    best_performing_categories: List[str] = []
    worst_performing_categories: List[str] = []

class EnrichedEvaluationMetricsModel(BaseModel):
    accuracy_at_1: float
    accuracy_at_2: float
    accuracy_at_3: float
    weighted_accuracy: float
    exact_match_at_2: float
    exact_match_at_3: float
    precision: float
    recall: float
    f1_score: float
    average_confidence: float
    total_predictions: int
    correct_predictions: int
    model_used: Optional[str] = None
    total_participant_processing_time_ms: Optional[float] = None # Changed to float for safety
    average_participant_processing_time_ms: Optional[float] = None # Changed to float
    total_participant_cost_dkk: Optional[float] = None
    total_participant_tokens_used: Optional[float] = None # Changed to float
    dashboard_evaluation_time_ms: Optional[float] = None # Changed to float

class DashboardParticipant(BaseModel):
    id: str
    name: str
    submittedAt: str # This is an ISO string, consider parsing to datetime if needed
    metrics: EnrichedEvaluationMetricsModel

class DashboardResponse(BaseModel):
    success: bool
    participant: DashboardParticipant