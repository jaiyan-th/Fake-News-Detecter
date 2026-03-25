"""
Password hashing and verification service using bcrypt
"""
import bcrypt

class PasswordService:
    """Password hashing and verification using bcrypt"""
    
    BCRYPT_ROUNDS = 12  # Work factor
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with salt
        Returns: bcrypt hash string
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against hash using constant-time comparison
        Returns: True if password matches
        """
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

# Global instance
password_service = PasswordService()
