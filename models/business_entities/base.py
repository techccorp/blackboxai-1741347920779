"""
Base models and utility classes for business entities
"""
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime

class PyObjectId(ObjectId):
    """Custom type for handling MongoDB ObjectId fields in Pydantic models"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ContactInfo(BaseModel):
    """Contact information with phone and email"""
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{7,14}$')
    email: EmailStr

class NextOfKin(BaseModel):
    """Next of kin information for employees"""
    name: str = Field(..., min_length=2, max_length=100)
    relationship: str = Field(..., min_length=2, max_length=50)
    contact: str = Field(..., pattern=r'^\+?[1-9]\d{7,14}$')

class SecurityStatus(BaseModel):
    """Security status information for user accounts"""
    password_history: List[str] = Field(default_factory=list)
    last_password_change: datetime = Field(default_factory=datetime.utcnow)
    failed_login_attempts: int = Field(0, ge=0)
    account_locked_until: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None

class PayRate(BaseModel):
    """
    Pay rate structure for employees
    
    Can include fortnight, monthly, or annual rates
    """
    fortnight_rate: Optional[float] = Field(None, ge=0)
    monthly_rate: Optional[float] = Field(None, ge=0)
    per_annum_rate: Optional[float] = Field(None, ge=0)

    @validator('*', pre=True)
    def round_decimals(cls, v):
        """Round all monetary values to 2 decimal places"""
        return round(v, 2) if isinstance(v, float) else v
