"""
Configuration management for Fake News Detection Backend
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # API Keys
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    SERPAPI_KEY = os.environ.get('SERPAPI_KEY')  # Google News via SerpAPI
    
    # Security configuration
    FAKE_NEWS_API_KEY = os.environ.get('FAKE_NEWS_API_KEY')  # Master API key for the service
    ALLOW_NO_API_KEY = os.environ.get('ALLOW_NO_API_KEY', 'true').lower() == 'true'  # For development
    
    # Database configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    
    # Ensure database directory exists
    os.makedirs(DATABASE_DIR, exist_ok=True)
    
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or os.path.join(DATABASE_DIR, 'news.db')
    
    # Model configuration
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL') or 'all-MiniLM-L6-v2'
    
    # API limits
    NEWS_API_LIMIT = int(os.environ.get('NEWS_API_LIMIT', '15'))
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '10'))
    
    @staticmethod
    def validate_config():
        """Validate configuration - allow running without API keys for demo"""
        # For demo purposes, we'll allow running without API keys
        # The system will work with reduced functionality
        missing_keys = []
        
        if not Config.GROQ_API_KEY:
            print("⚠️  Warning: GROQ_API_KEY not set. LLM features will use fallback explanations.")
        
        if not Config.NEWS_API_KEY:
            print("⚠️  Warning: NEWS_API_KEY not set. News fetching will use mock data.")
        
        return True