#!/usr/bin/env python3
"""
SQLite Database Configuration and Management
Replaces MongoDB with SQLite for easier setup
"""

import sqlite3
import os
import datetime
import json
import hashlib
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

# Database file path
# Database file path
if os.environ.get('VERCEL'):
    DB_PATH = os.path.join('/tmp', 'fake_news.db')
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'fake_news.db')

class DatabaseManager:
    """SQLite database manager for the fake news detector"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    role TEXT DEFAULT 'user'
                )
            ''')
            
            # Create predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    news TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence REAL DEFAULT 0.85,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'Web Interface',
                    category TEXT DEFAULT 'General',
                    tags TEXT DEFAULT '[]',
                    language TEXT DEFAULT 'en',
                    word_count INTEGER DEFAULT 0,
                    character_count INTEGER DEFAULT 0,
                    content_hash TEXT,
                    entities TEXT DEFAULT '{}',
                    model_version TEXT DEFAULT '1.0',
                    user_agent TEXT DEFAULT '',
                    ip_address TEXT DEFAULT '',
                    processing_time REAL DEFAULT 0.0,
                    probabilities TEXT DEFAULT '{}',
                    source_url TEXT DEFAULT '',
                    article_title TEXT DEFAULT '',
                    credibility_score REAL DEFAULT 0.5,
                    sentiment TEXT DEFAULT 'neutral',
                    emotional_score REAL DEFAULT 0.0,
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_username ON predictions(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_prediction ON predictions(prediction)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_content_hash ON predictions(content_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    def create_user(self, username: str, email: str, password_hash: str, role: str = 'user') -> bool:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, password, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, password_hash, role))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def update_user_password(self, username: str, password_hash: str) -> bool:
        """Update user password"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET password = ? WHERE username = ?', (password_hash, username))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_prediction(self, prediction_data: Dict) -> int:
        """Create a new prediction record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert complex data to JSON strings
            tags_json = json.dumps(prediction_data.get('tags', []))
            entities_json = json.dumps(prediction_data.get('entities', {}))
            probabilities_json = json.dumps(prediction_data.get('probabilities', {}))
            
            cursor.execute('''
                INSERT INTO predictions (
                    username, news, prediction, confidence, timestamp, source, category,
                    tags, language, word_count, character_count, content_hash, entities,
                    model_version, user_agent, ip_address, processing_time, probabilities,
                    source_url, article_title, credibility_score, sentiment, emotional_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_data['username'],
                prediction_data['news'],
                prediction_data['prediction'],
                prediction_data.get('confidence', 0.85),
                prediction_data.get('timestamp', datetime.datetime.now()),
                prediction_data.get('source', 'Web Interface'),
                prediction_data.get('category', 'General'),
                tags_json,
                prediction_data.get('language', 'en'),
                prediction_data.get('word_count', 0),
                prediction_data.get('character_count', 0),
                prediction_data.get('content_hash', ''),
                entities_json,
                prediction_data.get('model_version', '1.0'),
                prediction_data.get('user_agent', ''),
                prediction_data.get('ip_address', ''),
                prediction_data.get('processing_time', 0.0),
                probabilities_json,
                prediction_data.get('source_url', ''),
                prediction_data.get('article_title', ''),
                prediction_data.get('credibility_score', 0.5),
                prediction_data.get('sentiment', 'neutral'),
                prediction_data.get('emotional_score', 0.0)
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_predictions(self, username: str = None, limit: int = 50, offset: int = 0, 
                       search: str = None, prediction_filter: str = None, 
                       sort_by: str = 'timestamp', sort_order: str = 'desc') -> List[Dict]:
        """Get predictions with filtering and pagination"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            query = 'SELECT * FROM predictions'
            params = []
            conditions = []
            
            if username:
                conditions.append('username = ?')
                params.append(username)
            
            if search:
                conditions.append('(news LIKE ? OR username LIKE ?)')
                params.extend([f'%{search}%', f'%{search}%'])
            
            if prediction_filter and prediction_filter.upper() in ['REAL', 'FAKE']:
                conditions.append('prediction = ?')
                params.append(prediction_filter.upper())
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            # Add sorting
            sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
            query += f' ORDER BY {sort_by} {sort_direction}'
            
            # Add pagination
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries and parse JSON fields
            predictions = []
            for row in rows:
                pred = dict(row)
                pred['tags'] = json.loads(pred['tags']) if pred['tags'] else []
                pred['entities'] = json.loads(pred['entities']) if pred['entities'] else {}
                pred['probabilities'] = json.loads(pred['probabilities']) if pred['probabilities'] else {}
                # Handle new fields with defaults for backward compatibility
                pred['source_url'] = pred.get('source_url', '')
                pred['article_title'] = pred.get('article_title', '')
                pred['credibility_score'] = pred.get('credibility_score', 0.5)
                pred['sentiment'] = pred.get('sentiment', 'neutral')
                pred['emotional_score'] = pred.get('emotional_score', 0.0)
                predictions.append(pred)
            
            return predictions
    
    def get_prediction_by_id(self, prediction_id: int) -> Optional[Dict]:
        """Get a single prediction by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM predictions WHERE id = ?', (prediction_id,))
            row = cursor.fetchone()
            
            if row:
                pred = dict(row)
                pred['tags'] = json.loads(pred['tags']) if pred['tags'] else []
                pred['entities'] = json.loads(pred['entities']) if pred['entities'] else {}
                pred['probabilities'] = json.loads(pred['probabilities']) if pred['probabilities'] else {}
                return pred
            return None
    
    def get_prediction_by_hash(self, content_hash: str) -> Optional[Dict]:
        """Get prediction by content hash"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM predictions WHERE content_hash = ?', (content_hash,))
            row = cursor.fetchone()
            
            if row:
                pred = dict(row)
                pred['tags'] = json.loads(pred['tags']) if pred['tags'] else []
                pred['entities'] = json.loads(pred['entities']) if pred['entities'] else {}
                pred['probabilities'] = json.loads(pred['probabilities']) if pred['probabilities'] else {}
                return pred
            return None
    
    def count_predictions(self, username: str = None, search: str = None, 
                         prediction_filter: str = None) -> int:
        """Count predictions with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM predictions'
            params = []
            conditions = []
            
            if username:
                conditions.append('username = ?')
                params.append(username)
            
            if search:
                conditions.append('(news LIKE ? OR username LIKE ?)')
                params.extend([f'%{search}%', f'%{search}%'])
            
            if prediction_filter and prediction_filter.upper() in ['REAL', 'FAKE']:
                conditions.append('prediction = ?')
                params.append(prediction_filter.upper())
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total predictions
            cursor.execute('SELECT COUNT(*) FROM predictions')
            total_predictions = cursor.fetchone()[0]
            
            # Predictions by type
            cursor.execute('SELECT prediction, COUNT(*) FROM predictions GROUP BY prediction')
            by_prediction = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Recent activity (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM predictions 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            recent_activity = cursor.fetchone()[0]
            
            # Top users
            cursor.execute('''
                SELECT username, COUNT(*) as count 
                FROM predictions 
                GROUP BY username 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_users = [{'username': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return {
                'total_predictions': total_predictions,
                'by_prediction': by_prediction,
                'recent_activity': recent_activity,
                'top_users': top_users
            }
    
    def delete_user_predictions(self, username: str) -> int:
        """Delete all predictions for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM predictions WHERE username = ?', (username,))
            conn.commit()
            return cursor.rowcount
    
    def create_sample_data(self):
        """Create sample data for testing"""
        sample_predictions = [
            {
                'username': 'demo_user',
                'news': 'Scientists at MIT have developed a new artificial intelligence system that can detect fake news with 95% accuracy. The system uses advanced natural language processing techniques to analyze text patterns and cross-reference information with reliable sources.',
                'prediction': 'REAL',
                'confidence': 0.92,
                'source': 'Tech News Daily',
                'category': 'Technology',
                'tags': ['technology', 'science'],
                'word_count': 35,
                'character_count': 234,
                'content_hash': hashlib.md5('Scientists at MIT...'.encode()).hexdigest()
            },
            {
                'username': 'demo_user',
                'news': 'BREAKING: Aliens have landed in Times Square and are demanding to speak with world leaders. Witnesses report seeing flying saucers and strange beings with green skin. The government is allegedly covering up the incident to prevent panic.',
                'prediction': 'FAKE',
                'confidence': 0.96,
                'source': 'Social Media',
                'category': 'General',
                'tags': ['politics'],
                'word_count': 38,
                'character_count': 245,
                'content_hash': hashlib.md5('BREAKING: Aliens...'.encode()).hexdigest()
            }
        ]
        
        for pred_data in sample_predictions:
            try:
                self.create_prediction(pred_data)
            except Exception as e:
                print(f"Warning: Could not create sample prediction: {e}")

# Global database instance
db = DatabaseManager()

def get_db() -> DatabaseManager:
    """Get the global database instance"""
    return db