"""
Database models for RAG pipeline observability.

Tables
------
rag_analysis_logs  – one row per pipeline run (STEP 11)
rag_metrics        – one row per pipeline run with computed metrics (STEP 11)
"""

from datetime import datetime
from models.user import db


class RAGAnalysisLog(db.Model):
    """Stores every RAG pipeline execution for full traceability."""
    __tablename__ = "rag_analysis_logs"

    id              = db.Column(db.Integer, primary_key=True)
    request_id      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    input_text      = db.Column(db.Text,       nullable=False)
    claim           = db.Column(db.Text,       nullable=True)
    verdict         = db.Column(db.String(20), nullable=False)
    confidence      = db.Column(db.Float,      nullable=False)   # 0-1
    latency_ms      = db.Column(db.Float,      nullable=True)
    retrieval_count = db.Column(db.Integer,    default=0)
    support_count   = db.Column(db.Integer,    default=0)
    contradict_count= db.Column(db.Integer,    default=0)
    gap_type        = db.Column(db.String(50), nullable=True)
    created_at      = db.Column(db.DateTime,   default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "request_id":       self.request_id,
            "claim":            self.claim,
            "verdict":          self.verdict,
            "confidence":       round(self.confidence * 100, 1),
            "latency_ms":       self.latency_ms,
            "retrieval_count":  self.retrieval_count,
            "support_count":    self.support_count,
            "contradict_count": self.contradict_count,
            "gap_type":         self.gap_type,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
        }


class RAGMetrics(db.Model):
    """Stores computed pipeline metrics for monitoring and calibration."""
    __tablename__ = "rag_metrics"

    id                  = db.Column(db.Integer, primary_key=True)
    request_id          = db.Column(db.String(64), nullable=False, index=True)
    retrieval_accuracy  = db.Column(db.Float, nullable=True)   # relevant / total
    latency_ms          = db.Column(db.Float, nullable=True)
    confidence_score    = db.Column(db.Float, nullable=True)   # 0-100
    evidence_coverage   = db.Column(db.Integer, default=0)     # supporting sources
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "request_id":         self.request_id,
            "retrieval_accuracy": self.retrieval_accuracy,
            "latency_ms":         self.latency_ms,
            "confidence_score":   self.confidence_score,
            "evidence_coverage":  self.evidence_coverage,
        }
