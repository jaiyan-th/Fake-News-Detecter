"""
Authentication service - core business logic
"""
import re
from datetime import datetime
from typing import Optional, Tuple
from models.user import User, db
from services.password_service import password_service
from services.email_service import email_service
import logging
import threading

# Use standard logging
logger = logging.getLogger('fake_news_detector.auth')

class AuthService:
    """Core authentication business logic"""
    
    def register_user(self, email: str, password: str, name: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Register new user with email/password
        Returns: (user, error_message)
        """
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None, "An account with this email already exists"
        
        # Validate password strength
        is_valid, error_msg = self.validate_password_strength(password)
        if not is_valid:
            return None, error_msg
        
        # Create user
        user = User(email=email, name=name)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Send welcome email (synchronous for now to avoid app context issues)
            try:
                email_service.send_welcome_email(user)
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
            
            logger.info(f"User registered successfully: {email}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed for {email}: {str(e)}")
            return None, "Registration failed"
    
    def login_user(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with email/password
        Returns: (user, error_message)
        """
        user = User.query.filter_by(email=email).first()
        
        # Generic error message for security
        generic_error = "Invalid credentials"
        
        if not user:
            logger.warning(f"Login attempt for non-existent email: {email}")
            return None, generic_error
        
        # Check if account is locked
        if user.is_locked():
            logger.warning(f"Login attempt for locked account: {email}")
            return None, "Account temporarily locked due to multiple failed login attempts"
        
        # Verify password
        if not user.check_password(password):
            self.record_failed_login(user)
            logger.warning(f"Failed login attempt for {email}")
            return None, generic_error
        
        # Successful login
        self.record_successful_login(user)
        
        # Send login notification (synchronous for now)
        try:
            login_time = datetime.utcnow()
            email_service.send_login_notification(user, login_time)
        except Exception as e:
            logger.error(f"Failed to send login notification: {str(e)}")
        
        logger.info(f"User logged in successfully: {email}")
        return user, None
    
    def login_with_google(self, google_id: str, email: str, name: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate or register user via Google OAuth
        Returns: (user, error_message)
        """
        # Check if user exists with this Google ID
        user = User.query.filter_by(google_id=google_id).first()
        
        if user:
            # Existing user - update last login
            self.record_successful_login(user)
            
            # Send login notification (synchronous)
            try:
                login_time = datetime.utcnow()
                email_service.send_login_notification(user, login_time)
            except Exception as e:
                logger.error(f"Failed to send login notification: {str(e)}")
            
            logger.info(f"User logged in via Google: {email}")
            return user, None
        
        # Check if email already exists (link accounts)
        user = User.query.filter_by(email=email).first()
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            db.session.commit()
            self.record_successful_login(user)
            
            # Send login notification (synchronous)
            try:
                login_time = datetime.utcnow()
                email_service.send_login_notification(user, login_time)
            except Exception as e:
                logger.error(f"Failed to send login notification: {str(e)}")
            
            logger.info(f"Google account linked for existing user: {email}")
            return user, None
        
        # New user - create account
        user = User(email=email, name=name, google_id=google_id)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Send welcome email (synchronous)
            try:
                email_service.send_welcome_email(user)
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
            
            logger.info(f"New user registered via Google: {email}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Google registration failed for {email}: {str(e)}")
            return None, "Registration failed"
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements
        Returns: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def check_account_locked(self, user: User) -> bool:
        """Check if account is temporarily locked"""
        return user.is_locked()
    
    def record_failed_login(self, user: User) -> None:
        """Record failed login attempt and lock if threshold exceeded"""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= 5:
            user.lock_account(duration_minutes=15)
            logger.warning(f"Account locked due to failed login attempts: {user.email}")
        
        db.session.commit()
    
    def record_successful_login(self, user: User) -> None:
        """Update last login timestamp and reset failed attempts"""
        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0
        
        # Auto-unlock if was locked
        if user.is_locked():
            user.unlock_account()
        
        db.session.commit()
    
    def change_password(self, user: User, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Change user password
        Returns: (success, error_message)
        """
        # Verify current password
        if not user.check_password(current_password):
            logger.warning(f"Failed password change attempt for {user.email}: incorrect current password")
            return False, "Current password is incorrect"
        
        # Validate new password strength
        is_valid, error_msg = self.validate_password_strength(new_password)
        if not is_valid:
            return False, error_msg
        
        # Check if new password is same as current
        if user.check_password(new_password):
            return False, "New password must be different from current password"
        
        # Update password
        try:
            user.set_password(new_password)
            db.session.commit()
            
            # Send password change notification
            try:
                email_service.send_password_change_notification(user)
            except Exception as e:
                logger.error(f"Failed to send password change notification: {str(e)}")
            
            logger.info(f"Password changed successfully for user: {user.email}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Password change failed for {user.email}: {str(e)}")
            return False, "Failed to change password"

# Global instance
auth_service = AuthService()
