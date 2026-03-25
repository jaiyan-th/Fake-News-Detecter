"""
API key management service
"""

import os
import hashlib
import secrets
from typing import Dict, Optional, Set
from datetime import datetime, timedelta

class APIKeyManager:
    """Service for managing API keys and authentication"""
    
    def __init__(self):
        """Initialize API key manager"""
        self.api_keys = {}  # key_hash -> key_info
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from environment or configuration"""
        # For demo purposes, we'll use environment variables
        # In production, use a secure key management system
        
        # Check for master API key in environment
        master_key = os.getenv('FAKE_NEWS_API_KEY')
        if master_key:
            key_hash = self._hash_key(master_key)
            self.api_keys[key_hash] = {
                'name': 'master_key',
                'created_at': datetime.now(),
                'last_used': None,
                'usage_count': 0,
                'rate_limit_multiplier': 1.0,
                'permissions': {'analyze', 'health'},
                'active': True
            }
        
        # Add default frontend client key for development
        frontend_key = 'frontend-client-key'
        key_hash = self._hash_key(frontend_key)
        self.api_keys[key_hash] = {
            'name': 'frontend_client',
            'created_at': datetime.now(),
            'last_used': None,
            'usage_count': 0,
            'rate_limit_multiplier': 1.0,
            'permissions': {'analyze', 'health'},
            'active': True
        }
        
        # For development/testing, allow requests without API key
        # This should be disabled in production
        self.allow_no_key = os.getenv('ALLOW_NO_API_KEY', 'false').lower() == 'true'
    
    def _hash_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def validate_api_key(self, api_key: Optional[str], endpoint: str = 'analyze') -> Dict[str, any]:
        """
        Validate API key and check permissions
        
        Returns:
            Dict with validation result and key info
        """
        result = {
            'valid': False,
            'key_info': None,
            'error': None,
            'rate_limit_multiplier': 1.0
        }
        
        # If no API key provided
        if not api_key:
            if self.allow_no_key:
                result['valid'] = True
                result['key_info'] = {
                    'name': 'anonymous',
                    'permissions': {'analyze', 'health'},
                    'rate_limit_multiplier': 1.0
                }
                return result
            else:
                result['error'] = 'API key required'
                return result
        
        # Validate API key format
        if not isinstance(api_key, str) or len(api_key) < 10:
            result['error'] = 'Invalid API key format'
            return result
        
        # Hash and lookup key
        key_hash = self._hash_key(api_key)
        key_info = self.api_keys.get(key_hash)
        
        if not key_info:
            result['error'] = 'Invalid API key'
            return result
        
        # Check if key is active
        if not key_info.get('active', True):
            result['error'] = 'API key deactivated'
            return result
        
        # Check permissions
        required_permission = endpoint
        if required_permission not in key_info.get('permissions', set()):
            result['error'] = f'API key lacks permission for {endpoint}'
            return result
        
        # Update usage statistics
        key_info['last_used'] = datetime.now()
        key_info['usage_count'] = key_info.get('usage_count', 0) + 1
        
        result['valid'] = True
        result['key_info'] = key_info
        result['rate_limit_multiplier'] = key_info.get('rate_limit_multiplier', 1.0)
        
        return result
    
    def generate_api_key(self, name: str, permissions: Set[str] = None) -> str:
        """Generate a new API key"""
        if permissions is None:
            permissions = {'analyze', 'health'}
        
        # Generate secure random key
        api_key = 'fndb_' + secrets.token_urlsafe(32)
        key_hash = self._hash_key(api_key)
        
        # Store key info
        self.api_keys[key_hash] = {
            'name': name,
            'created_at': datetime.now(),
            'last_used': None,
            'usage_count': 0,
            'rate_limit_multiplier': 1.0,
            'permissions': permissions,
            'active': True
        }
        
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = self._hash_key(api_key)
        if key_hash in self.api_keys:
            self.api_keys[key_hash]['active'] = False
            return True
        return False
    
    def get_key_stats(self) -> Dict[str, any]:
        """Get API key usage statistics"""
        active_keys = sum(1 for key_info in self.api_keys.values() if key_info.get('active', True))
        total_usage = sum(key_info.get('usage_count', 0) for key_info in self.api_keys.values())
        
        return {
            'total_keys': len(self.api_keys),
            'active_keys': active_keys,
            'total_usage': total_usage,
            'allow_no_key': self.allow_no_key
        }

# Global API key manager instance
api_key_manager = APIKeyManager()