"""
SQLAlchemy ORM Models for Users and Verification History
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.db.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    verifications = relationship("VerificationHistory", back_populates="user", cascade="all, delete-orphan", order_by="desc(VerificationHistory.created_at)")

    def __repr__(self):
        return f"<User {self.email}>"


class VerificationHistory(Base):
    __tablename__ = "verification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_id = Column(String(64), index=True, nullable=False)
    input_type = Column(String(10), nullable=False)  # "url" or "text"
    input_content = Column(Text, nullable=False)

    verdict = Column(String(32), nullable=False)  # "REAL", "FALSE", "MISLEADING", "UNVERIFIED"
    confidence = Column(Integer, nullable=False)
    primary_claim = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    # JSON stored fields for full evidence replay
    evidence_summary_json = Column(JSON, nullable=True)
    sources_json = Column(JSON, nullable=True)
    pipeline_stages_json = Column(JSON, nullable=True)
    limitations_json = Column(JSON, nullable=True)

    source_agreement_percentage = Column(Float, default=0.0)
    processing_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="verifications")

    def __repr__(self):
        return f"<VerificationHistory id={self.id} verdict={self.verdict} user_id={self.user_id}>"
