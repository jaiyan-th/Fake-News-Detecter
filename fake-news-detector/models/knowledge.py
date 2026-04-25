"""
Vector Database model for RAG (Retrieval-Augmented Generation)
Stores previously verified articles and fact-checks as vectors
"""

from datetime import datetime
from pgvector.sqlalchemy import Vector
from models.user import db

class KnowledgeArticle(db.Model):
    """Knowledge base article for RAG similarity search"""
    __tablename__ = 'knowledge_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True, nullable=False, index=True)
    title = db.Column(db.String(512), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255), nullable=True)
    
    # Verification details
    verdict = db.Column(db.String(50), nullable=True) # REAL, FAKE, UNCERTAIN
    is_trusted = db.Column(db.Boolean, default=False)
    
    # The pgvector embedding column. 
    # all-MiniLM-L6-v2 outputs 384-dimensional vectors
    embedding = db.Column(Vector(384))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content[:200] + "..." if len(self.content) > 200 else self.content,
            'source': self.source,
            'verdict': self.verdict,
            'is_trusted': self.is_trusted,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
