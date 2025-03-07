"""
Password management utilities for employee security
"""
import re
import bcrypt
from datetime import datetime, timedelta

class PasswordManager:
    """
    Password management class that handles password validation,
    hashing, verification, and security policy enforcement.
    """
    
    def _validate_password_policy(self, password: str) -> bool:
        """
        Validate password against security policy
        
        Requirements:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        
        Returns:
            bool: True if password meets policy
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters long")
        
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
            
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
            
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one digit")
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")
            
        return True
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: BCrypt hash to check against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def hash_password(self, password: str) -> tuple:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password to hash
            
        Returns:
            tuple: (hashed_password, salt)
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8'), salt
    
    def check_password_age(self, last_change: datetime) -> bool:
        """
        Check if password needs rotation (90 days)
        
        Args:
            last_change: Datetime of last password change
            
        Returns:
            bool: True if password needs to be changed, False otherwise
        """
        return (datetime.utcnow() - last_change) > timedelta(days=90)