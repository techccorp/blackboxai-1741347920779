"""
Employee models for business entities
"""
import re
import bcrypt
from pydantic import BaseModel, Field, validator, root_validator, EmailStr
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from .base import PyObjectId, NextOfKin, SecurityStatus, PayRate
from .employment import EmploymentDetails, LeaveEntitlements, AccruedEmployment

try:
    from utils.security.password_manager import PasswordManager
except ImportError:
    # Fallback implementation if the module isn't available
    class PasswordManager:
        """Fallback password manager implementation"""
        def _validate_password_policy(self, password: str) -> bool:
            """Basic password policy validation"""
            if len(password) < 12:
                raise ValueError("Password must be at least 12 characters long")
            return True
            
        def verify_password(self, plain_password: str, hashed_password: str) -> bool:
            """Verify a password against its hash"""
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            
        def hash_password(self, password: str) -> tuple:
            """Hash a password using bcrypt"""
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8'), salt
            
        def check_password_age(self, last_change: datetime) -> bool:
            """Check if password needs rotation (90 days)"""
            return (datetime.utcnow() - last_change) > timedelta(days=90)

class EmployeeBase(BaseModel):
    """
    Base employee model with common fields
    
    This model contains fields common to all employee-related operations
    and serves as the foundation for more specific employee models.
    """
    linking_id: str = Field(..., pattern=r'^EMP-\d{4}-\d{4}-\d{6}$')
    payroll_id: str = Field(..., pattern=r'^D[A-Z]-\d{6}$')
    company_id: str = Field(..., pattern=r'^CNY-\d{4}$')
    company_name: str = Field(..., min_length=2, max_length=100)
    venue_id: str = Field(..., pattern=r'^VEN-\d{4}-\d{2}$')
    venue_name: str = Field(..., min_length=2, max_length=100)
    work_area_id: str = Field(..., pattern=r'^WAI-\d{4}-\d{4}$')
    work_area_name: str = Field(..., min_length=2, max_length=50)
    role_id: str = Field(..., pattern=r'^FOH-[A-Z]{3}-\d{3}$|^BOH-[A-Z]{3}-\d{3}$')
    role_name: str = Field(..., min_length=2, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    preferred_name: Optional[str] = Field(None, max_length=50)
    date_of_birth: datetime
    address: str = Field(..., min_length=5, max_length=200)
    suburb: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    post_code: str = Field(..., pattern=r'^\d{4}$')
    personal_contact: str = Field(..., pattern=r'^\+?[1-9]\d{7,14}$')
    next_of_kin: NextOfKin
    work_email: EmailStr
    permissions: List[str] = Field(default_factory=list)
    employment_details: Union[EmploymentDetails, Dict[str, Any]]
    leave_entitlements: Union[LeaveEntitlements, Dict[str, Any]]
    accrued_employment: Union[AccruedEmployment, Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('payroll_id')
    def validate_payroll_id(cls, v, values):
        """
        Validate that the payroll ID format matches the employee's work area
        
        The first letter after 'D' in the payroll ID must correspond to the 
        employee's work area. For example:
        - Bar: DB-123456
        - Kitchen: DK-123456
        - Restaurant: DR-123456
        
        Returns:
            str: Validated payroll ID
            
        Raises:
            ValueError: If payroll ID prefix doesn't match work area
        """
        work_area = values.get('work_area_name', '').lower()
        area_codes = {
            "admin": "A", "bar": "B", "cleaners": "C", "functions": "F",
            "guest services": "G", "house keeping": "H", "kitchen": "K",
            "maintenance": "M", "operations": "O", "restaurant": "R",
            "store room": "S", "venue": "V"
        }
        
        expected_code = area_codes.get(work_area)
        if expected_code and not v.startswith(f"D{expected_code}-"):
            raise ValueError(f"Payroll ID for {work_area} should start with 'D{expected_code}-'")
        return v

    @validator('work_email')
    def validate_work_email(cls, v, values):
        """
        Validate that work email matches the employee's payroll ID
        
        Work emails must use the payroll ID as the local part of the email address.
        For example, if payroll_id is "DB-123456", the email must be "DB-123456@domain.com"
        
        This ensures consistency between payroll IDs and email addresses,
        and helps prevent misassignment of email addresses.
        
        Returns:
            str: Validated work email
            
        Raises:
            ValueError: If email local part doesn't match payroll ID
        """
        payroll_id = values.get('payroll_id')
        if payroll_id and '@' in v:
            local, domain = v.split('@', 1)
            if local != payroll_id:
                raise ValueError(f"Work email should start with payroll ID: {payroll_id}@")
        return v

    @root_validator
    def validate_linking_id_components(cls, values):
        """
        Validate linking ID components match company and work area IDs
        
        The linking ID (EMP-XXXX-YYYY-ZZZZZZ) must have components that match:
        - XXXX must match the company_id's numeric portion
        - YYYY must match the work_area_id's numeric portion
        
        This ensures referential integrity between the employee and their
        assigned company and work area.
        
        Returns:
            Dict: Validated values
            
        Raises:
            ValueError: If linking ID components are inconsistent with company or work area
        """
        linking_id = values.get('linking_id', '')
        company_id = values.get('company_id', '')
        work_area_id = values.get('work_area_id', '')
        
        if linking_id and company_id and work_area_id:
            linking_parts = linking_id.split('-')
            if len(linking_parts) != 4:
                raise ValueError("Invalid linking ID format")
                
            company_num = company_id.split('-')[1] if '-' in company_id else ''
            work_area_num = work_area_id.split('-')[-1] if '-' in work_area_id else ''
            
            if linking_parts[1] != company_num:
                raise ValueError("Linking ID company component doesn't match company ID")
                
            if linking_parts[2] != work_area_num:
                raise ValueError("Linking ID work area component doesn't match work area ID")
                
        return values

    class Config:
        allow_population_by_field_name = True
        json_encoders = {PyObjectId: str}
        schema_extra = {
            "example": {
                "_id": "67c1246d02971bbe2f6e6fe4",
                "linking_id": "EMP-2976-3088-520242",
                "payroll_id": "DB-520242",
                "company_id": "CNY-2976",
                "company_name": "Melbourne Venue Co",
                "venue_id": "VEN-2976-30",
                "venue_name": "Black Jacks Smoke House",
                "work_area_id": "WAI-2976-3088",
                "work_area_name": "Bar",
                "role_id": "FOH-MGT-304",
                "role_name": "Bar Manager",
                "first_name": "Penelope",
                "last_name": "Pittstop",
                "preferred_name": "Penny",
                "date_of_birth": "1989-01-05T00:00:00.000Z",
                "address": "3 Funky Lane Rd",
                "suburb": "Hoppers Crossing",
                "state": "Victoria",
                "post_code": "3006",
                "personal_contact": "+61413928681",
                "next_of_kin": {
                    "name": "Janet Waldo",
                    "relationship": "mother",
                    "contact": "+61497332086"
                },
                "work_email": "DB-520242@gmail.com",
                "permissions": [],
                "employment_details": {
                    "hired_date": "2020-03-01T00:00:00.000Z",
                    "employment_type": "full time",
                    "pay_type": "salary",
                    "pay_rate": {
                        "fortnight_rate": 5000,
                        "monthly_rate": 10000,
                        "per_annum_rate": 85000
                    }
                },
                "leave_entitlements": {
                    "holiday_accrued": 171.0,
                    "holiday_taken": 0,
                    "sick_accrued": 85.5,
                    "sick_taken": 0
                },
                "accrued_employment": {
                    "days_employed": 411,
                    "unpaid_leave": 0,
                    "tax_withheld": 39587.67,
                    "salary_ytd": 121808.22
                }
            }
        }

class EmployeeCreate(EmployeeBase):
    """
    Employee creation model
    
    Used when creating a new employee record. Contains a plaintext password
    which will be hashed before storage.
    """
    password: str = Field(..., min_length=12, max_length=100)
    security_status: SecurityStatus = Field(default_factory=SecurityStatus)

    @validator('password')
    def validate_password(cls, v):
        """Validate password against security policy"""
        PasswordManager()._validate_password_policy(v)
        return v

class Employee(EmployeeBase):
    """
    Complete employee model with security features
    
    This is the main model for employee records, including security information
    and password management capabilities.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str = Field(..., min_length=60, max_length=100)
    security_status: SecurityStatus = Field(default_factory=SecurityStatus)

    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored bcrypt hash
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return PasswordManager().verify_password(password, self.hashed_password)

    def set_password(self, new_password: str) -> None:
        """
        Update password with security checks
        
        Performs validation including:
        - Password policy compliance
        - Password history check (prevent reuse)
        
        Args:
            new_password: New password to set
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        pm = PasswordManager()
        
        # Check password policy
        pm._validate_password_policy(new_password)
        
        # Check against password history
        if any(pm.verify_password(new_password, old) for old in self.security_status.password_history):
            raise ValueError("Password reuse detected")
            
        # Generate new hash
        new_hash, _ = pm.hash_password(new_password)
        
        # Update security status
        self.security_status.password_history = [new_hash] + self.security_status.password_history[:4]  # Keep last 5
        self.security_status.last_password_change = datetime.utcnow()
        self.hashed_password = new_hash

    def check_password_age(self) -> bool:
        """
        Check if password needs rotation
        
        Returns:
            bool: True if password needs to be changed, False otherwise
        """
        return PasswordManager().check_password_age(self.security_status.last_password_change)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {PyObjectId: str}
        schema_extra = {
            "example": {
                "_id": "67c1246d02971bbe2f6e6fe4",
                "linking_id": "EMP-2976-3088-520242",
                "payroll_id": "DB-520242",
                "company_id": "CNY-2976",
                "company_name": "Melbourne Venue Co",
                "venue_id": "VEN-2976-30",
                "venue_name": "Black Jacks Smoke House",
                "work_area_id": "WAI-2976-3088",
                "work_area_name": "Bar",
                "role_id": "FOH-MGT-304",
                "role_name": "Bar Manager",
                "first_name": "Penelope",
                "last_name": "Pittstop",
                "preferred_name": "Penny",
                "date_of_birth": "1989-01-05T00:00:00.000Z",
                "address": "3 Funky Lane Rd",
                "suburb": "Hoppers Crossing",
                "state": "Victoria",
                "post_code": "3006",
                "personal_contact": "+61413928681",
                "next_of_kin": {
                    "name": "Janet Waldo",
                    "relationship": "mother",
                    "contact": "+61497332086"
                },
                "work_email": "DB-520242@gmail.com",
                "hashed_password": "$2b$12$zb2Gll3w4ndkP92pVwHevO54xQWkhaFwmF2pBkW4jvG3k8LMIZiiW",
                "permissions": [],
                "employment_details": {
                    "hired_date": "2020-03-01T00:00:00.000Z",
                    "employment_type": "full time",
                    "pay_type": "salary",
                    "pay_rate": {
                        "fortnight_rate": 5000,
                        "monthly_rate": 10000,
                        "per_annum_rate": 85000
                    }
                },
                "leave_entitlements": {
                    "holiday_accrued": 171.0,
                    "holiday_taken": 0,
                    "sick_accrued": 85.5,
                    "sick_taken": 0
                },
                "accrued_employment": {
                    "days_employed": 411,
                    "unpaid_leave": 0,
                    "tax_withheld": 39587.67,
                    "salary_ytd": 121808.22
                },
                "security_status": {
                    "password_history": [],
                    "last_password_change": "2020-03-01T00:00:00.000Z",
                    "failed_login_attempts": 0,
                    "account_locked_until": None,
                    "mfa_enabled": False,
                }
            }
        }
