"""
User model for authentication system
"""
from datetime import datetime, timedelta
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth-only users
    name = db.Column(db.String(255), nullable=False)
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        from services.password_service import password_service
        self.password_hash = password_service.hash_password(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        if not self.password_hash:
            return False
        from services.password_service import password_service
        return password_service.verify_password(password, self.password_hash)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excludes password_hash)"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def lock_account(self, duration_minutes: int = 15) -> None:
        """Lock account for specified duration"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.is_active = False
    
    def unlock_account(self) -> None:
        """Unlock account"""
        self.locked_until = None
        self.is_active = True
        self.failed_login_attempts = 0
    
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        if datetime.utcnow() >= self.locked_until:
            # Auto-unlock if lock period expired
            self.unlock_account()
            return False
        return True
