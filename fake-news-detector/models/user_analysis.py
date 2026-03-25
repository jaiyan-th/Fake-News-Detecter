"""
User Analysis History Model
"""
from datetime import datetime
from models.user import db

class UserAnalysis(db.Model):
    """User analysis history model"""
    __tablename__ = 'user_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Analysis details
    input_type = db.Column(db.String(20), nullable=False)  # 'url' or 'text'
    input_content = db.Column(db.Text, nullable=False)  # URL or text snippet
    
    # Results
    verdict = db.Column(db.String(20), nullable=False)  # 'REAL', 'FAKE', 'UNCERTAIN'
    confidence = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    
    # Metadata
    matched_articles_count = db.Column(db.Integer, default=0)
    processing_time = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('analyses', lazy='dynamic'))
    
    def to_dict(self) -> dict:
        """Convert analysis to dictionary"""
        return {
            'id': self.id,
            'input_type': self.input_type,
            'input_preview': self.input_content[:100] + '...' if len(self.input_content) > 100 else self.input_content,
            'verdict': self.verdict,
            'confidence': round(self.confidence * 100, 1),  # Convert to percentage
            'explanation': self.explanation,
            'matched_articles_count': self.matched_articles_count,
            'processing_time': round(self.processing_time, 2) if self.processing_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
