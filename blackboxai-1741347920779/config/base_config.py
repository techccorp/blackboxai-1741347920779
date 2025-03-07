# ------------------------------------------------------------
#                  config/base_config.py
# ------------------------------------------------------------
import os
import warnings
from datetime import timedelta
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Dict, List, Optional, Tuple

# Load environment variables from .env file
load_dotenv()

class BaseConfig(BaseSettings):
    """Production-grade configuration with validation and environment separation"""
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False

class AppConfig(BaseConfig):
    FLASK_ENV: str = Field(..., env='FLASK_ENV')
    REMEMBER_COOKIE_SECURE: bool = Field(..., env='REMEMBER_COOKIE_SECURE')
    REDIS_HOST: str = Field(..., env='REDIS_HOST')
    REDIS_PORT: int = Field(..., env='REDIS_PORT')
    REDIS_USERNAME: str = Field(..., env='REDIS_USERNAME')
    REDIS_PASSWORD: str = Field(..., env='REDIS_PASSWORD')
    REDIS_DB: int = Field(..., env='REDIS_DB')
    REDIS_KEY_PREFIX: str = Field(..., env='REDIS_KEY_PREFIX')
    REDIS_DEFAULT_EXPIRY: int = Field(..., env='REDIS_DEFAULT_EXPIRY')
    REDIS_LONG_EXPIRY: int = Field(..., env='REDIS_LONG_EXPIRY')
    GOOGLE_API_KEY: str = Field(..., env='GOOGLE_API_KEY')
    GOOGLE_CLIENT_ID: str = Field(..., env='GOOGLE_CLIENT_ID')
    GOOGLE_PROJECT_ID: str = Field(..., env='GOOGLE_PROJECT_ID')
    GOOGLE_CLIENT_SECRET: str = Field(..., env='GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI: str = Field(..., env='GOOGLE_REDIRECT_URI')
    BCRYPT_LOG_ROUNDS: int = Field(..., env='BCRYPT_LOG_ROUNDS')
    CORS_ORIGINS: str = Field(..., env='CORS_ORIGINS')
    GOOGLE_CALENDAR_SCOPES: str = Field(..., env='GOOGLE_CALENDAR_SCOPES')
    GOOGLE_GMAIL_SCOPES: str = Field(..., env='GOOGLE_GMAIL_SCOPES')
    CALENDAR_ID: str = Field(..., env='CALENDAR_ID')
    GOOGLE_CLIENT_SECRETS: str = Field(..., env='GOOGLE_CLIENT_SECRETS')
    GOOGLE_TOKEN_PATH: str = Field(..., env='GOOGLE_TOKEN_PATH')
    # Core Application Settings
    ENV: str = Field('production', env='FLASK_ENV')
    SECRET_KEY: str = Field(..., min_length=32, env='SECRET_KEY')
    DEBUG: bool = Field(False, env='FLASK_DEBUG')
    TESTING: bool = False
    
    # Network Configuration
    HOST: str = Field('0.0.0.0', env='FLASK_HOST')
    PORT: int = Field(5000, gt=1024, lt=65535, env='FLASK_PORT')
    USE_SSL: bool = False
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    @property
    def ssl_context(self) -> Optional[Tuple[str, str]]:
        return (self.SSL_CERT_PATH, self.SSL_KEY_PATH) if self.USE_SSL else None

    # Database Configuration
    MONGO_URI: str = Field(..., pattern=r'^mongodb(\+srv)?://', env='MONGO_URI')
    MONGO_DBNAME: str = Field('MyCookBook', min_length=1, env='MONGO_DBNAME')
    MONGO_MAX_POOL_SIZE: int = Field(100, gt=0)
    MONGO_MIN_POOL_SIZE: int = Field(10, gt=0)
    MONGO_CONNECT_TIMEOUT_MS: int = Field(30000, gt=0)
    MONGO_SOCKET_TIMEOUT_MS: int = Field(30000, gt=0)
    MONGO_TLS: bool = Field(True)  # Enable TLS for MongoDB Atlas
    MONGO_TLS_CA_FILE: Optional[str] = None
    
    @validator('MONGO_TLS', pre=True)
    def validate_tls(cls, v, values):
        """Enable TLS if using MongoDB Atlas (SRV connection)"""
        mongo_uri = values.get('MONGO_URI', '')
        if mongo_uri.startswith('mongodb+srv://'):
            return True
        return v
    
    # Business Collections
    COLLECTION_BUSINESSES: str = 'business_entities'
    COLLECTION_BUSINESS_VENUES: str = 'business_venues'
    COLLECTION_BUSINESS_USERS: str = 'business_users'
    COLLECTION_BUSINESS_ROLES: str = 'business_roles'
    COLLECTION_EMPLOYMENT_ROLES: str = 'employment_roles'
    
    # Security Settings
    SESSION_LIFETIME: timedelta = Field(timedelta(days=7))
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    PASSWORD_RESET_TIMEOUT: int = 900  # 15 minutes in seconds
    
    # File Handling
    UPLOAD_FOLDER: str = Field('uploads', env='UPLOAD_FOLDER')
    MAX_UPLOAD_SIZE: int = Field(10485760, description="10MB in bytes")  # 10MB
    ALLOWED_MIME_TYPES: Dict[str, List[str]] = {
        'image': ['png', 'jpg', 'jpeg'],
        'document': ['pdf']
    }
    
    # Rate Limiting
    RATE_LIMITS: Dict[str, str] = {
        'default': '200/day;50/hour',
        'auth': '10/minute;100/day',
        'api': '1000/minute'
    }
    
    # Logging Configuration
    LOG_LEVEL: str = Field('INFO', pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE: Optional[str] = '/var/log/app.log'
    
    # External Services
    SMTP_SERVER: str = 'smtp.gmail.com'
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = 'noreply@myfoodieapp.com'
    
    # Validation
    @validator('ENV')
    def validate_env(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'ENV must be one of {allowed}')
        return v
    
    @validator('DEBUG', pre=True)
    def validate_debug(cls, v, values):
        if values.get('ENV') == 'production' and v:
            warnings.warn("Debug mode should not be enabled in production", RuntimeWarning)
        return v

class DevelopmentConfig(AppConfig):
    DEBUG: bool = True
    MONGO_URI: str = 'mongodb://localhost:27017'
    LOG_LEVEL: str = 'DEBUG'
    SESSION_COOKIE_SECURE: bool = False

class ProductionConfig(AppConfig):
    pass

def get_config(env: Optional[str] = None) -> AppConfig:
    """Factory method for environment-specific configurations"""
    env = env or os.getenv('FLASK_ENV', 'production')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig
    }
    return configs[env]()

# Initialize configuration
config = get_config()
