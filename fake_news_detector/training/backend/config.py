"""
Configuration settings for the Fake News Detector application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB settings
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/fake_news_app'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Rate limiting settings
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5000',
        'http://127.0.0.1:5000'
    ]
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    # Model settings
    MODEL_PATH = os.path.join('model', 'model.pkl')
    VECTORIZER_PATH = os.path.join('model', 'vectorizer.pkl')
    
    # Text processing settings
    MIN_TEXT_LENGTH = 10
    MAX_TEXT_LENGTH = 10000
    MAX_BATCH_SIZE = 10
    
    # API settings
    API_VERSION = '1.0'
    API_TITLE = 'Fake News Detector API'
    API_DESCRIPTION = 'API for fake news detection with card grid interface'
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Performance settings
    ENABLE_CACHING = True
    ENABLE_COMPRESSION = True
    ENABLE_ETAG = True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Disable some security features for development
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN'  # Less restrictive for development
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Stricter settings for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # Production MongoDB URI
    MONGODB_URI = os.environ.get('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable must be set in production")
    
    # Production CORS origins
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Enhanced security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    }

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    MONGODB_URI = 'mongodb://localhost:27017/fake_news_app_test'
    
    # Disable rate limiting for tests
    RATE_LIMIT_STORAGE_URL = 'memory://'
    
    # Faster cache timeout for tests
    CACHE_DEFAULT_TIMEOUT = 1

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_BATCH_PREDICTION': os.environ.get('ENABLE_BATCH_PREDICTION', 'true').lower() == 'true',
    'ENABLE_CACHING': os.environ.get('ENABLE_CACHING', 'true').lower() == 'true',
    'ENABLE_RATE_LIMITING': os.environ.get('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
    'ENABLE_ANALYTICS': os.environ.get('ENABLE_ANALYTICS', 'false').lower() == 'true',
    'ENABLE_CONTENT_DEDUPLICATION': os.environ.get('ENABLE_CONTENT_DEDUPLICATION', 'true').lower() == 'true'
}

# API Rate limits (requests per minute)
RATE_LIMITS = {
    'predict': int(os.environ.get('RATE_LIMIT_PREDICT', 30)),
    'batch_predict': int(os.environ.get('RATE_LIMIT_BATCH', 5)),
    'search': int(os.environ.get('RATE_LIMIT_SEARCH', 60)),
    'cards': int(os.environ.get('RATE_LIMIT_CARDS', 120))
}