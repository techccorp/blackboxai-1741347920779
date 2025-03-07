"""
Compatibility utilities for business entity models

This module provides utilities to ensure backward compatibility 
with older model formats and facilitate migration to the new structure.
"""
from typing import Dict, Any, Union, List, Optional
from datetime import datetime
import bcrypt

from .employee import Employee, EmployeeCreate, EmployeeBase
from .employment import EmploymentDetails, LeaveEntitlements, AccruedEmployment
from .base import SecurityStatus, PayRate

def convert_business_user_to_employee(business_user: Dict[str, Any]) -> Employee:
    """
    Convert a BusinessUser dictionary to an Employee model
    
    This utility function helps migrate from the old BusinessUser format
    to the new structured Employee model.
    
    Args:
        business_user: Dictionary containing BusinessUser data
        
    Returns:
        Employee: Converted Employee model instance
    """
    # Create nested models
    security_status = SecurityStatus(
        password_history=business_user.get('security_status', {}).get('password_history', []),
        last_password_change=business_user.get('security_status', {}).get('last_password_change', datetime.utcnow()),
        failed_login_attempts=business_user.get('security_status', {}).get('failed_login_attempts', 0),
        account_locked_until=business_user.get('security_status', {}).get('account_locked_until'),
        mfa_enabled=business_user.get('security_status', {}).get('mfa_enabled', False),
        mfa_secret=business_user.get('security_status', {}).get('mfa_secret')
    )
    
    # Extract employment details
    ed = business_user.get('employment_details', {})
    employment_details = EmploymentDetails(
        hired_date=ed.get('hired_date', datetime.utcnow()),
        employment_type=ed.get('employment_type', 'full time'),
        pay_type=ed.get('pay_type', 'salary'),
        pay_rate=PayRate(**ed.get('pay_rate', {'per_annum_rate': 0})),
        termination_date=ed.get('termination_date'),
        termination_reason=ed.get('termination_reason')
    )
    
    # Extract leave entitlements
    le = business_user.get('leave_entitlements', {})
    leave_entitlements = LeaveEntitlements(
        holiday_accrued=le.get('holiday_accrued', 0.0),
        holiday_taken=le.get('holiday_taken', 0.0),
        sick_accrued=le.get('sick_accrued', 0.0),
        sick_taken=le.get('sick_taken', 0.0),
        carers_accrued=le.get('carers_accrued', 0.0),
        carers_taken=le.get('carers_taken', 0.0),
        bereavement_accrued=le.get('bereavement_accrued', 0.0),
        bereavement_taken=le.get('bereavement_taken', 0.0),
        maternity_entitlement=le.get('maternity_entitlement', 0.0),
        maternity_taken=le.get('maternity_taken', 0.0),
        unpaid_leave_taken=le.get('unpaid_leave_taken', 0.0)
    )
    
    # Extract accrued employment
    ae = business_user.get('accrued_employment', {})
    accrued_employment = AccruedEmployment(
        days_employed=ae.get('days_employed', 0),
        unpaid_leave=ae.get('unpaid_leave', 0.0),
        tax_withheld=ae.get('tax_withheld', 0.0),
        salary_ytd=ae.get('salary_ytd', 0.0),
        tax_withheld_ytd=ae.get('tax_withheld_ytd', 0.0)
    )
    
    # Create employee model
    employee_data = {k: v for k, v in business_user.items() if k not in [
        'security_status', 'employment_details', 'leave_entitlements', 'accrued_employment'
    ]}
    
    # Add structured components
    employee_data.update({
        'security_status': security_status,
        'employment_details': employment_details,
        'leave_entitlements': leave_entitlements,
        'accrued_employment': accrued_employment
    })
    
    # Handle password conversion if needed
    if 'password' in employee_data and 'hashed_password' not in employee_data:
        password = employee_data.pop('password')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        employee_data['hashed_password'] = hashed.decode('utf-8')
    
    return Employee(**employee_data)

def convert_employee_to_business_user(employee: Employee) -> Dict[str, Any]:
    """
    Convert an Employee model to a BusinessUser dictionary
    
    This function is useful for backward compatibility with systems 
    that still expect the old BusinessUser format.
    
    Args:
        employee: Employee model instance
        
    Returns:
        Dict: Dictionary in BusinessUser format
    """
    # Start with basic dict conversion
    employee_dict = employee.dict(by_alias=True)
    
    # Convert nested models to dictionaries
    if isinstance(employee_dict.get('employment_details'), dict):
        # Already a dict, leave as is
        pass
    else:
        employee_dict['employment_details'] = employee.employment_details.dict()

    if isinstance(employee_dict.get('leave_entitlements'), dict):
        # Already a dict, leave as is
        pass
    else:
        employee_dict['leave_entitlements'] = employee.leave_entitlements.dict()
        
    if isinstance(employee_dict.get('accrued_employment'), dict):
        # Already a dict, leave as is
        pass
    else:
        employee_dict['accrued_employment'] = employee.accrued_employment.dict()
    
    # Convert security status
    employee_dict['security_status'] = employee.security_status.dict()
    
    return employee_dict
