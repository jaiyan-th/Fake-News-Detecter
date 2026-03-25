"""
Database models and operations
"""

import sqlite3
import os
from typing import Optional, List, Dict
from datetime import datetime
from contextlib import contextmanager

class Database:
    """Database service for persistent storage"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_directory_exists()
        self._init_database()
    
    def _ensure_directory_exists(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            with self.get_connection() as conn:
                # Analysis results table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        summary TEXT,
                        verdict TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        explanation TEXT,
                        matched_articles TEXT,
                        key_claims TEXT,
                        processing_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index on URL for faster lookups
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_url 
                    ON analysis(url)
                ''')
                
                # Create index on created_at for time-based queries
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_created_at 
                    ON analysis(created_at)
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Database initialization failed: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def store_analysis(self, url: str, summary: str, verdict: str, 
                      confidence: float, explanation: str = "", 
                      matched_articles: List[Dict] = None, 
                      key_claims: List[str] = None,
                      processing_time: float = 0.0) -> Optional[int]:
        """
        Store analysis result in database
        Uses INSERT OR REPLACE to handle URL uniqueness constraint
        
        Returns:
            Analysis ID if successful, None otherwise
        """
        try:
            import json
            
            matched_articles_json = json.dumps(matched_articles or [])
            key_claims_json = json.dumps(key_claims or [])
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO analysis 
                    (url, summary, verdict, confidence, explanation, 
                     matched_articles, key_claims, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url, summary, verdict, confidence, explanation,
                    matched_articles_json, key_claims_json, processing_time
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
                
                return analysis_id
                
        except Exception as e:
            print(f"Analysis storage failed: {str(e)}")
            return None
    
    def get_analysis_by_url(self, url: str) -> Optional[Dict]:
        """Retrieve most recent analysis for a URL"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM analysis 
                    WHERE url = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (url,))
                
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except Exception as e:
            print(f"Analysis retrieval failed: {str(e)}")
            return None
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get recent analysis results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, url, verdict, confidence, created_at 
                    FROM analysis 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Recent analyses retrieval failed: {str(e)}")
            return []
    
    def get_analysis_stats(self) -> Dict:
        """Get analysis statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total analyses
                cursor.execute('SELECT COUNT(*) as total FROM analysis')
                total = cursor.fetchone()['total']
                
                # Verdict distribution
                cursor.execute('''
                    SELECT verdict, COUNT(*) as count 
                    FROM analysis 
                    GROUP BY verdict
                ''')
                verdict_stats = {row['verdict']: row['count'] for row in cursor.fetchall()}
                
                # Average confidence
                cursor.execute('SELECT AVG(confidence) as avg_confidence FROM analysis')
                avg_confidence = cursor.fetchone()['avg_confidence'] or 0.0
                
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM analysis 
                    WHERE created_at < datetime('now', '-{} days')
                '''.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")
            return 0