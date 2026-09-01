"""
Pydantic Schemas for System Health & Diagnostics
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class DependencyHealth(BaseModel):
    status: str = Field(default="operational", description="operational, degraded, unavailable, or unconfigured")
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="healthy, degraded, or unhealthy")
    application: str = "running"
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
