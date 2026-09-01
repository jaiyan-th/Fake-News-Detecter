"""
Pydantic Schemas for Verification Request and Response
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, model_validator, HttpUrl


class VerdictEnum(str, Enum):
    REAL = "REAL"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    UNVERIFIED = "UNVERIFIED"


class StanceEnum(str, Enum):
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    NEUTRAL = "NEUTRAL"


class VerificationRequest(BaseModel):
    url: Optional[str] = Field(default=None, description="Direct URL of the news article to verify")
    text: Optional[str] = Field(default=None, description="Pasted news claim or article content")

    @model_validator(mode="after")
    def validate_input_exclusive(self):
        url_present = bool(self.url and self.url.strip())
        text_present = bool(self.text and self.text.strip())

        if not url_present and not text_present:
            raise ValueError("Please provide either a news 'url' OR news 'text' to verify.")
        if url_present and text_present:
            raise ValueError("Please provide either 'url' OR 'text', not both simultaneously.")
        return self


class ClaimInfo(BaseModel):
    primary_claim: str = Field(description="The central factual claim extracted from input")
    secondary_claims: List[str] = Field(default_factory=list, description="Additional verifiable assertions")
    entities: List[str] = Field(default_factory=list, description="Key people, places, organizations, or laws")
    timeframe: Optional[str] = Field(default=None, description="Reported date or temporal context")


class EvidenceSource(BaseModel):
    source_name: str
    domain: str
    title: str
    url: str
    published_at: Optional[str] = None
    stance: StanceEnum = StanceEnum.NEUTRAL
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_snippet: str
    credibility_tier: str = Field(default="STANDARD_NEWS")
    search_provider: str = Field(default="newsapi")


class EvidenceSummary(BaseModel):
    supporting: int = 0
    contradicting: int = 0
    neutral: int = 0
    total_sources_evaluated: int = 0


class PipelineStage(BaseModel):
    stage: str
    status: str
    duration_ms: float
    details: Optional[Dict[str, Any]] = None


class VerificationResponse(BaseModel):
    verdict: VerdictEnum
    confidence: int = Field(ge=0, le=100, description="Verification Confidence score (0-100)")
    confidence_label: str = "Verification Confidence"
    claim: ClaimInfo
    summary: str
    explanation: str
    evidence_summary: EvidenceSummary
    sources: List[EvidenceSource] = Field(default_factory=list)
    source_agreement_percentage: float = Field(ge=0.0, le=100.0, default=0.0)
    limitations: List[str] = Field(default_factory=list)
    pipeline_stages: List[PipelineStage] = Field(default_factory=list)
    processing_time_ms: float
