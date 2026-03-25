"""
Authentication routes - registration, login, logout, OAuth
"""
from flask import Blueprint, request, jsonify, session, redirect
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User, db
from services.auth_service import auth_service
from services.oauth_service import oauth_service
import logging
import secrets

# Use standard logging
logger = logging.getLogger('fake_news_detector.auth_routes')

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        # Validate required fields
        if not email or not password or not name:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Register user
        user, error = auth_service.register_user(email, password, name)
        
        if error:
            status_code = 409 if 'already exists' in error else 400
            return jsonify({'success': False, 'error': error}), status_code
        
        # Create session
        login_user(user, remember=True)
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate required fields
        if not email or not password:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Authenticate user
        user, error = auth_service.login_user(email, password)
        
        if error:
            return jsonify({'success': False, 'error': error}), 401
        
        # Create session
        login_user(user, remember=True)
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint"""
    try:
        logout_user()
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user info"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/google', methods=['GET'])
def google_oauth():
    """Initiate Google OAuth flow"""
    try:
        if not oauth_service.is_configured:
            return jsonify({'success': False, 'error': 'Google OAuth not configured'}), 503
        
        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Get authorization URL
        auth_url = oauth_service.get_authorization_url(state)
        
        return jsonify({
            'success': True,
            'authorization_url': auth_url
        }), 200
        
    except Exception as e:
        logger.error(f"OAuth initiation error: {str(e)}")
        return jsonify({'success': False, 'error': 'OAuth initialization failed'}), 500

@auth_bp.route('/google/callback', methods=['GET'])
def google_oauth_callback():
    """Google OAuth callback endpoint"""
    try:
        if not oauth_service.is_configured:
            return jsonify({'success': False, 'error': 'Google OAuth not configured'}), 503
        
        # Verify state token (CSRF protection)
        state = request.args.get('state')
        stored_state = session.get('oauth_state')
        
        if not state or state != stored_state:
            logger.warning("OAuth state mismatch - possible CSRF attack")
            return jsonify({'success': False, 'error': 'Invalid state parameter'}), 400
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'success': False, 'error': 'No authorization code provided'}), 400
        
        # Exchange code for token
        token = oauth_service.exchange_code_for_token(code)
        
        # Get user info from Google
        user_info = oauth_service.get_user_info(token['access_token'])
        
        # Authenticate or register user
        user, error = auth_service.login_with_google(
            google_id=user_info['id'],
            email=user_info['email'],
            name=user_info['name']
        )
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
        
        # Create session
        login_user(user, remember=True)
        
        # Redirect to frontend
        return redirect('http://localhost:3000/?auth=success')
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return redirect('http://localhost:3000/?auth=error')

@auth_bp.route('/refresh', methods=['POST'])
@login_required
def refresh_session():
    """Refresh user session"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        # Validate required fields
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Validate new password length
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
        
        # Change password
        success, error = auth_service.change_password(current_user, current_password, new_password)
        
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500
