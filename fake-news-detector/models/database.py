"""
Database models and operations using SQLAlchemy
"""

import os
import json
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.user import db

class AnalysisCache(db.Model):
    """Anonymous analysis results table"""
    __tablename__ = 'analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True, nullable=False, index=True)
    summary = db.Column(db.Text)
    verdict = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text)
    matched_articles = db.Column(db.Text)
    key_claims = db.Column(db.Text)
    processing_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Database:
    """Database service for persistent storage"""
    
    def __init__(self, db_path: str = None):
        # We don't need db_path anymore since we use SQLAlchemy's connection
        self.db_path = db_path
    
    def store_analysis(self, url: str, summary: str, verdict: str, 
                      confidence: float, explanation: str = "", 
                      matched_articles: List[Dict] = None, 
                      key_claims: List[str] = None,
                      processing_time: float = 0.0) -> Optional[int]:
        """Store or update analysis result in database"""
        try:
            matched_articles_json = json.dumps(matched_articles or [])
            key_claims_json = json.dumps(key_claims or [])
            
            # Check if exists
            record = AnalysisCache.query.filter_by(url=url).first()
            if record:
                record.summary = summary
                record.verdict = verdict
                record.confidence = confidence
                record.explanation = explanation
                record.matched_articles = matched_articles_json
                record.key_claims = key_claims_json
                record.processing_time = processing_time
                record.created_at = datetime.utcnow()
            else:
                record = AnalysisCache(
                    url=url, summary=summary, verdict=verdict,
                    confidence=confidence, explanation=explanation,
                    matched_articles=matched_articles_json,
                    key_claims=key_claims_json, processing_time=processing_time
                )
                db.session.add(record)
                
            db.session.commit()
            return record.id
                
        except Exception as e:
            db.session.rollback()
            print(f"Analysis storage failed: {str(e)}")
            return None
    
    def get_analysis_by_url(self, url: str) -> Optional[Dict]:
        """Retrieve most recent analysis for a URL"""
        try:
            record = AnalysisCache.query.filter_by(url=url).order_by(desc(AnalysisCache.created_at)).first()
            if record:
                return {
                    'id': record.id,
                    'url': record.url,
                    'summary': record.summary,
                    'verdict': record.verdict,
                    'confidence': record.confidence,
                    'explanation': record.explanation,
                    'matched_articles': record.matched_articles,
                    'key_claims': record.key_claims,
                    'processing_time': record.processing_time,
                    'created_at': record.created_at
                }
            return None
        except Exception as e:
            print(f"Analysis retrieval failed: {str(e)}")
            return None
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get recent analysis results"""
        try:
            records = AnalysisCache.query.order_by(desc(AnalysisCache.created_at)).limit(limit).all()
            return [
                {
                    'id': r.id, 'url': r.url, 'verdict': r.verdict,
                    'confidence': r.confidence, 'created_at': r.created_at
                }
                for r in records
            ]
        except Exception as e:
            print(f"Recent analyses retrieval failed: {str(e)}")
            return []
    
    def get_analysis_stats(self) -> Dict:
        """Get analysis statistics"""
        try:
            total = db.session.query(func.count(AnalysisCache.id)).scalar() or 0
            
            verdict_counts = db.session.query(
                AnalysisCache.verdict, func.count(AnalysisCache.id)
            ).group_by(AnalysisCache.verdict).all()
            verdict_stats = {v: c for v, c in verdict_counts}
            
            avg_confidence = db.session.query(func.avg(AnalysisCache.confidence)).scalar() or 0.0
            
            return {
                'total_analyses': total,
                'verdict_distribution': verdict_stats,
                'average_confidence': round(avg_confidence, 3)
            }
        except Exception as e:
            print(f"Stats retrieval failed: {str(e)}")
            return {
                'total_analyses': 0,
                'verdict_distribution': {},
                'average_confidence': 0.0
            }
    
    def cleanup_old_analyses(self, days_old: int = 30) -> int:
        """Remove analyses older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = AnalysisCache.query.filter(AnalysisCache.created_at < cutoff_date).delete()
            db.session.commit()
            return deleted_count
        except Exception as e:
            db.session.rollback()
            print(f"Cleanup failed: {str(e)}")
            return 0