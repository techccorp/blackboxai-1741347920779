"""
Employment details models for business entities
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict
from .base import PayRate

class EmploymentDetails(BaseModel):
    """
    Employment details for an employee
    
    Contains information about employment terms, hiring date,
    and compensation structure.
    """
    hired_date: datetime
    employment_type: str = Field(..., pattern='^(full time|part time|casual)$')
    pay_type: str = Field(..., pattern='^(salary|hourly)$')
    pay_rate: PayRate
    termination_date: Optional[datetime] = None
    termination_reason: Optional[str] = None

class LeaveEntitlements(BaseModel):
    """
    Leave entitlements for an employee
    
    Tracks accrued and used leave across various leave types
    """
    holiday_accrued: float = Field(..., ge=0)
    holiday_taken: float = Field(..., ge=0)
    sick_accrued: float = Field(..., ge=0)
    sick_taken: float = Field(..., ge=0)
    carers_accrued: float = Field(..., ge=0)
    carers_taken: float = Field(..., ge=0)
    bereavement_accrued: float = Field(..., ge=0)
    bereavement_taken: float = Field(..., ge=0)
    maternity_entitlement: float = Field(..., ge=0)
    maternity_taken: float = Field(..., ge=0)
    unpaid_leave_taken: float = Field(..., ge=0)

class AccruedEmployment(BaseModel):
    """
    Accrued employment metrics
    
    Tracks employment duration, tax, and salary information
    """
    days_employed: int = Field(..., ge=0)
    unpaid_leave: float = Field(..., ge=0)
    tax_withheld: float = Field(..., ge=0)
    salary_ytd: float = Field(..., ge=0)
    tax_withheld_ytd: float = Field(..., ge=0)
