#--------------------------------------------#
#            utils/auth/auth_utils.py        #
#--------------------------------------------#
from typing import Dict, Optional, Tuple, Any
import logging
import re
import bcrypt
from datetime import datetime, timedelta
from flask import current_app, session, g
import jwt
try:
    from google.oauth2 import credentials
    from google.auth.transport.requests import Request
    from config.google_oauth_config import GoogleOAuthConfig
    from utils.google_utils import validate_google_token
    HAS_GOOGLE_OAUTH = True
except ImportError:
    HAS_GOOGLE_OAUTH = False
from utils.security_utils import generate_secure_token
from utils.logging_utils import log_security_event

logger = logging.getLogger(__name__)

# Standalone functions for direct imports
def validate_payroll_id(payroll_id: str) -> bool:
    """
    Validate the format of a payroll ID.
    
    Valid format: D{work_area_letter}-{6 digits}
    Example: DK-308020 (Kitchen), DB-631353 (Bar)
    
    Args:
        payroll_id: The payroll ID to validate
        
    Returns:
        bool: True if the payroll ID is valid, False otherwise
    """
    # Check if the payroll ID matches the pattern
    pattern = r'^D[KBROFPSGW]-\d{6}$'
    return bool(re.match(pattern, payroll_id))

def hash_password(password: str) -> str:
    """
    Hash a password for secure storage.
    
    Args:
        password: The plaintext password to hash
        
    Returns:
        str: The hashed password
    """
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(stored_hash: str, password: str) -> bool:
    """
    Check if a plaintext password matches a stored hash.
    
    Args:
        stored_hash: The stored hashed password
        password: The plaintext password to check
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password check error: {str(e)}")
        return False

def generate_token(user_data: Dict[str, Any], expiry_hours: int = 8) -> str:
    """
    Generate a JWT token for authentication.
    
    Args:
        user_data: Dictionary containing user information
        expiry_hours: Token expiry time in hours
        
    Returns:
        str: Encoded JWT token
    """
    try:
        # Create payload with user data and expiry
        payload = {
            # Essential user identifiers
            'payroll_id': user_data['payroll_id'],
            'email': user_data.get('work_email', ''),
            
            # Role and permission context
            'role': user_data.get('role', ''),
            
            # Business context
            'business_id': user_data.get('company_id', ''),
            'venue_id': user_data.get('venue_id', ''),
            'work_area_id': user_data.get('work_area_id', ''),
            
            # Token metadata
            'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
            'iat': datetime.utcnow()
        }
        
        # Encode and return token
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        raise

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Decoded token payload or None if invalid
    """
    try:
        # Decode and verify token
        return jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None

class AuthError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, error_code: str = 'AUTH_ERROR'):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AuthUtils:
    """Authentication utility functions"""

    @staticmethod
    def create_session_token(user_data: Dict[str, Any]) -> str:
        """
        Create JWT session token for user
        """
        try:
            if HAS_GOOGLE_OAUTH:
                token_expiry = GoogleOAuthConfig.TOKEN_EXPIRY_SECONDS
            else:
                token_expiry = timedelta(hours=8)

            # Support both formats of user data
            if 'pay_details' in user_data:
                payload = {
                    'payroll_id': user_data['pay_details']['payroll_id'],
                    'email_work': user_data['pay_details']['email_work'],
                    'role': user_data['role'],
                    'business_id': user_data['linked']['business_id'],
                    'venue_id': user_data['linked']['venue_id'],
                    'work_area_id': user_data['work_area_id'],
                    'exp': datetime.utcnow() + token_expiry,
                    'iat': datetime.utcnow()
                }
            else:
                payload = {
                    'payroll_id': user_data.get('payroll_id'),
                    'email_work': user_data.get('work_email', ''),
                    'role': user_data.get('role', ''),
                    'business_id': user_data.get('company_id', ''),
                    'venue_id': user_data.get('venue_id', ''),
                    'work_area_id': user_data.get('work_area_id', ''),
                    'exp': datetime.utcnow() + token_expiry,
                    'iat': datetime.utcnow()
                }
            
            token = jwt.encode(
                payload,
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            
            log_security_event(
                'token_created',
                payload['payroll_id'],
                'Session token created successfully'
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating session token: {str(e)}")
            raise AuthError("Failed to create session token")

    @staticmethod
    def verify_session_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT session token
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthError("Session token has expired", "TOKEN_EXPIRED")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid session token", "INVALID_TOKEN")
        except Exception as e:
            logger.error(f"Error verifying session token: {str(e)}")
            raise AuthError("Failed to verify session token")

    @staticmethod
    def initialize_session(user_data: Dict[str, Any], google_credentials: Optional[Dict] = None) -> None:
        """
        Initialize user session with both application and Google credentials
        """
        try:
            # Support both formats of user data
            if 'pay_details' in user_data:
                session['user'] = {
                    'payroll_id': user_data['pay_details']['payroll_id'],
                    'email_work': user_data['pay_details']['email_work'],
                    'role': user_data['role'],
                    'business_id': user_data['linked']['business_id'],
                    'venue_id': user_data['linked']['venue_id'],
                    'work_area_id': user_data['work_area_id']
                }
            else:
                session['user'] = {
                    'payroll_id': user_data.get('payroll_id'),
                    'email_work': user_data.get('work_email', ''),
                    'role': user_data.get('role', ''),
                    'business_id': user_data.get('company_id', ''),
                    'venue_id': user_data.get('venue_id', ''),
                    'work_area_id': user_data.get('work_area_id', '')
                }
            
            if google_credentials and HAS_GOOGLE_OAUTH:
                session[GoogleOAuthConfig.SESSION_KEYS['credentials']] = google_credentials
                session[GoogleOAuthConfig.SESSION_KEYS['last_refresh']] = datetime.utcnow().isoformat()
            
            g.user = session['user']
            
        except Exception as e:
            logger.error(f"Error initializing session: {str(e)}")
            raise AuthError("Failed to initialize session")

    @staticmethod
    def refresh_google_credentials() -> Optional[object]:
        """
        Refresh Google credentials if expired
        """
        if not HAS_GOOGLE_OAUTH:
            return None
            
        try:
            creds_dict = session.get(GoogleOAuthConfig.SESSION_KEYS['credentials'])
            if not creds_dict:
                return None

            creds = credentials.Credentials(**creds_dict)
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
                # Update session with refreshed credentials
                session[GoogleOAuthConfig.SESSION_KEYS['credentials']] = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                session[GoogleOAuthConfig.SESSION_KEYS['last_refresh']] = datetime.utcnow().isoformat()
                
                log_security_event(
                    'token_refreshed',
                    session['user']['payroll_id'],
                    'Google credentials refreshed successfully'
                )
                
            return creds
            
        except Exception as e:
            logger.error(f"Error refreshing Google credentials: {str(e)}")
            return None

    @staticmethod
    def validate_login_attempt(payroll_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate login attempt against rate limiting
        """
        try:
            attempts_key = f"login_attempts_{payroll_id}"
            attempts = session.get(attempts_key, [])
            current_time = datetime.utcnow()
            
            # Default values if GoogleOAuthConfig is not available
            login_attempt_window = 300  # 5 minutes
            max_login_attempts = 5
            
            if HAS_GOOGLE_OAUTH:
                login_attempt_window = GoogleOAuthConfig.LOGIN_ATTEMPT_WINDOW
                max_login_attempts = GoogleOAuthConfig.MAX_LOGIN_ATTEMPTS
                
            # Clean up old attempts
            attempts = [
                attempt for attempt in attempts
                if (current_time - attempt).total_seconds() < login_attempt_window
            ]
            
            if len(attempts) >= max_login_attempts:
                return False, "Too many login attempts. Please try again later."
                
            attempts.append(current_time)
            session[attempts_key] = attempts
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating login attempt: {str(e)}")
            return False, "Error validating login attempt"

    @staticmethod
    def clear_login_attempts(payroll_id: str) -> None:
        """
        Clear login attempts on successful login
        """
        try:
            attempts_key = f"login_attempts_{payroll_id}"
            session.pop(attempts_key, None)
        except Exception as e:
            logger.error(f"Error clearing login attempts: {str(e)}")

    @staticmethod
    def end_session() -> None:
        """
        End user session and clean up
        """
        try:
            if 'user' in session:
                log_security_event(
                    'logout',
                    session['user']['payroll_id'],
                    'User logged out successfully'
                )
            
            # Clear all session data
            session.clear()
            
            # Clear request context
            if hasattr(g, 'user'):
                delattr(g, 'user')
                
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            raise AuthError("Failed to end session")

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """
        Get current user from session
        """
        return session.get('user')

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if user is authenticated
        """
        return 'user' in session

    @staticmethod
    def has_role(role: str) -> bool:
        """
        Check if current user has specific role
        """
        user = session.get('user', {})
        return user.get('role') == role

    @staticmethod
    def has_permission(permission: str) -> bool:
        """
        Check if current user has specific permission
        """
        user = session.get('user', {})
        return permission in user.get('permissions', [])
        
    @staticmethod
    def validate_payroll_id(payroll_id: str) -> bool:
        """
        Validate payroll ID format using standalone function
        """
        return validate_payroll_id(payroll_id)
        
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using standalone function
        """
        return hash_password(password)
        
    @staticmethod
    def check_password(stored_hash: str, password: str) -> bool:
        """
        Verify a password using standalone function
        """
        return check_password(stored_hash, password)