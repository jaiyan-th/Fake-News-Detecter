"""
Fake News Detection Backend - Main Flask Application
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from datetime import timedelta
from config import Config
from services.rate_limiter import rate_limiter
from services.api_keys import api_key_manager
from services.security import security_validator
from models.user import db, User
import os

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access - return JSON instead of redirect"""
    from flask import jsonify
    return jsonify({
        'success': False,
        'error': 'Authentication required',
        'message': 'Please log in to access this resource'
    }), 401

def create_app():
    """Create and configure Flask application"""
    from config import Config as AppConfig
    
    app = Flask(__name__)
    app.config.from_object(AppConfig)
    
    # Authentication configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = not app.debug  # True in production
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Database configuration
    supabase_url = os.environ.get('SUPABASE_DB_URL')
    
    if supabase_url:
        # SQLAlchemy requires postgresql:// or postgresql+psycopg2://
        app.config['SQLALCHEMY_DATABASE_URI'] = supabase_url
        print(f"Database URI: Supabase PostgreSQL connected")
    else:
        database_path = AppConfig.DATABASE_PATH
        
        # Ensure the path is absolute and properly formatted for SQLite URI
        if not os.path.isabs(database_path):
            database_path = os.path.abspath(database_path)
        
        # Convert Windows path to URI format (forward slashes)
        database_path = database_path.replace('\\', '/')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
        print(f"Database URI: sqlite:///{database_path}")
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    # Don't set login_view - we'll handle unauthorized access with JSON responses
    login_manager.login_view = None
    
    # Create database tables (with error handling)
    with app.app_context():
        try:
            # Import models to ensure they're registered
            from models.user_analysis import UserAnalysis
            from models.knowledge import KnowledgeArticle
            from models.database import AnalysisCache
            db.create_all()
            print("[OK] Database tables created/verified")
        except Exception as e:
            print(f"[WARNING] Database initialization warning: {e}")
            print("  Database will be created on first use")
    
    # Configure CORS with credentials support
    CORS(app, 
         origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
         methods=['GET', 'POST', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-API-Key'],
         supports_credentials=True)  # Enable credentials for session cookies
    
    # Global error handlers
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.VALIDATION_ERROR,
            user_message="Invalid request format"
        )
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.AUTHENTICATION_ERROR,
            user_message="Authentication required"
        )
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.VALIDATION_ERROR,
            user_message="Endpoint not found"
        )
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.VALIDATION_ERROR,
            user_message="HTTP method not allowed for this endpoint"
        )
    
    @app.errorhandler(413)
    def handle_payload_too_large(error):
        """Handle 413 Payload Too Large errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.VALIDATION_ERROR,
            user_message="Request payload too large"
        )
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.RATE_LIMIT_ERROR,
            user_message="Rate limit exceeded, please try again later"
        )
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle 500 Internal Server Error"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.INTERNAL_ERROR,
            user_message="Internal server error occurred"
        )
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle 503 Service Unavailable errors"""
        from services.error_handler import error_handler, ErrorType
        return error_handler.create_error_response(
            error, ErrorType.API_ERROR,
            user_message="Service temporarily unavailable"
        )
    
    # Add security middleware
    @app.before_request
    def security_middleware():
        """Apply security checks before each request"""
        
        # Skip security for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Skip rate limiting for static files (CSS, JS, images, favicon)
        if request.endpoint in ['serve_index', 'serve_static']:
            return None
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Rate limiting
        allowed, rate_info = rate_limiter.is_allowed(client_ip)
        if not allowed:
            response = jsonify({
                'error': 'Rate limit exceeded',
                'message': rate_info.get('message', 'Too many requests'),
                'retry_after': rate_info.get('retry_after', 60)
            })
            
            # Add security headers
            headers = security_validator.get_security_headers()
            for header, value in headers.items():
                response.headers[header] = value
            
            response.status_code = 429
            return response
        
        # API key validation (only for analyze endpoint)
        if request.endpoint and 'analyze' in request.endpoint:
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]  # Remove 'Bearer ' prefix
            
            validation_result = api_key_manager.validate_api_key(api_key, 'analyze')
            if not validation_result['valid']:
                response = jsonify({
                    'error': 'Authentication failed',
                    'message': validation_result['error']
                })
                
                # Add security headers
                headers = security_validator.get_security_headers()
                for header, value in headers.items():
                    response.headers[header] = value
                
                response.status_code = 401
                return response
    
    @app.after_request
    def after_request(response):
        """Add security and rate limit headers to all responses"""
        
        # Get client IP for rate limit headers
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Add rate limit headers
        rate_headers = rate_limiter.get_rate_limit_headers(client_ip)
        for header, value in rate_headers.items():
            response.headers[header] = value
        
        # Add security headers (if not already added)
        security_headers = security_validator.get_security_headers()
        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value
        
        return response
    
    # Register routes
    from routes.analyze import analyze_bp
    from routes.auth import auth_bp
    from routes.history import history_bp
    app.register_blueprint(analyze_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(history_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)