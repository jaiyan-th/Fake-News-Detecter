"""
Pydantic Schemas for Verification History
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.verification import (
    ClaimInfo, EvidenceSource, EvidenceSummary, PipelineStage, VerdictEnum
)


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    verification_id: str
    input_type: str
    input_content: str
    verdict: VerdictEnum
    confidence: int
    primary_claim: str
    summary: Optional[str] = None
    source_agreement_percentage: float = 0.0
    total_sources: int = 0
    processing_time_ms: float = 0.0
    created_at: datetime


class HistoryList(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class HistoryDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    verification_id: str
    input_type: str
    input_content: str
    verdict: VerdictEnum
    confidence: int
    confidence_label: str = "Verification Confidence"
    claim: ClaimInfo
    summary: str
    explanation: str
    evidence_summary: EvidenceSummary
    sources: List[EvidenceSource] = Field(default_factory=list)
    source_agreement_percentage: float = 0.0
    limitations: List[str] = Field(default_factory=list)
    pipeline_stages: List[PipelineStage] = Field(default_factory=list)
    processing_time_ms: float
    created_at: datetime
