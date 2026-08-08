"""
Vector Database model for RAG (Retrieval-Augmented Generation)
Stores previously verified articles and fact-checks as vectors
"""

import os
from datetime import datetime
from models.user import db

# pgvector is only available when running against PostgreSQL.
# Fall back to a plain Text column when it is not installed / not needed
# (e.g. the SQLite development path on Render free tier).
try:
    from pgvector.sqlalchemy import Vector as _Vector
    _embedding_column = db.Column(_Vector(384))
    _PGVECTOR_AVAILABLE = True
except Exception:
    _PGVECTOR_AVAILABLE = False


class KnowledgeArticle(db.Model):
    """Knowledge base article for RAG similarity search"""
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True, nullable=False, index=True)
    title = db.Column(db.String(512), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255), nullable=True)

    # Verification details
    verdict = db.Column(db.String(50), nullable=True)  # REAL, FAKE, UNCERTAIN
    is_trusted = db.Column(db.Boolean, default=False)

    # Vector embedding – uses pgvector when available, otherwise plain Text
    if _PGVECTOR_AVAILABLE:
        from pgvector.sqlalchemy import Vector
        embedding = db.Column(Vector(384))
    else:
        embedding = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'source': self.source,
            'verdict': self.verdict,
            'is_trusted': self.is_trusted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
