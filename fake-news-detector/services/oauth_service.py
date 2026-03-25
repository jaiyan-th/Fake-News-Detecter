"""
Google OAuth 2.0 integration service
"""
import os
from authlib.integrations.requests_client import OAuth2Session
import logging

# Use standard logging
logger = logging.getLogger('fake_news_detector.oauth')

class OAuthService:
    """Google OAuth 2.0 integration"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/auth/google/callback')
        
        self.authorization_endpoint = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_endpoint = 'https://oauth2.googleapis.com/token'
        self.userinfo_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
        
        self.scope = 'openid email profile'
        
        # Check if OAuth is configured
        self.is_configured = bool(self.client_id and self.client_secret)
        if not self.is_configured:
            logger.warning("Google OAuth not configured - OAuth sign-in will not be available")
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL
        Returns: Authorization URL with state parameter
        """
        if not self.is_configured:
            raise ValueError("Google OAuth not configured")
        
        session = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
        authorization_url, _ = session.create_authorization_url(
            self.authorization_endpoint,
            state=state
        )
        
        return authorization_url
    
    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for access token
        Returns: Token response dict
        """
        if not self.is_configured:
            raise ValueError("Google OAuth not configured")
        
        session = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri
        )
        
        token = session.fetch_token(
            self.token_endpoint,
            code=code,
            client_secret=self.client_secret
        )
        
        return token
    
    def get_user_info(self, access_token: str) -> dict:
        """
        Retrieve user profile from Google
        Returns: User info dict with id, email, name
        """
        session = OAuth2Session(token={'access_token': access_token})
        response = session.get(self.userinfo_endpoint)
        response.raise_for_status()
        
        user_info = response.json()
        
        return {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name', user_info.get('email', '').split('@')[0])
        }

# Global instance
oauth_service = OAuthService()
