"""
Authentication Service
Handles password hashing (bcrypt) and JWT token generation/validation.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import jwt
from backend.core.config import settings

logger = logging.getLogger("news_verification.auth_service")

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        expire_minutes: int = None
    ):
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self.expire_minutes = expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against the stored bcrypt hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """Generate bcrypt hash for password"""
        return pwd_context.hash(password)

    def create_access_token(self, user_id: int, email: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
        """Generate a signed JWT access token"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.expire_minutes)
        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.info("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
