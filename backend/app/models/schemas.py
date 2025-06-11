from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"  
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class ConversationType(str, Enum):
    CONSULTATION = "consultation"
    SERVICE = "service"
    MIXED = "mixed"

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.now)

class ProcessingStatus(BaseModel):
    job_id: str
    status: ProcessingStatusEnum
    progress: int = Field(ge=0, le=100)
    message: str
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ScoredItem(BaseModel):
    category: str
    item: str
    score: int = Field(ge=1, le=5)
    max_score: int = 5
    justification: str
    evidence: List[str] = []
    improvement_guidance: Optional[str] = None

class ConversationSummary(BaseModel):
    conversation_type: ConversationType
    subject: str
    total_score: int
    max_total_score: int
    pass_status: bool
    key_strengths: List[str]
    areas_for_improvement: List[str]
    action_plan: List[str]

class AuditResults(BaseModel):
    job_id: str
    filename: str
    summary: ConversationSummary
    scored_items: List[ScoredItem]
    transcript: str
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now) 