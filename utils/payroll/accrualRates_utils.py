"""
Utility functions for leave accrual calculations and service period handling.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Union, Any

# Standard leave accrual rates (hours per year for full-time employees)
LEAVE_ACCRUAL_RATES = {
    'holiday': Decimal('152'),       # 4 weeks (38 hours x 4)
    'sick': Decimal('76'),           # 2 weeks
    'carers': Decimal('38'),         # 1 week
    'bereavement': Decimal('15.2')   # 2 days
}

# Long service leave accrual rate (varies by state, using VIC as default)
LONG_SERVICE_ACCRUAL_RATE = {
    'vic': Decimal('60'),            # 1.67 weeks per year after 7 years
    'nsw': Decimal('43.3'),          # 1.14 weeks per year after 10 years
    'qld': Decimal('65'),            # 1.71 weeks per year after 10 years
    'sa': Decimal('43.3'),           # 1.14 weeks per year after 10 years
    'wa': Decimal('43.3'),           # 1.14 weeks per year after 10 years
    'tas': Decimal('50'),            # 1.32 weeks per year after 10 years
    'act': Decimal('60'),            # 1.67 weeks per year after 7 years
    'nt': Decimal('43.3')            # 1.14 weeks per year after 10 years
}

def calculate_service_period(hired_date: datetime) -> Decimal:
    """
    Calculate service period in years based on hired date.
    
    Args:
        hired_date: Date employee was hired
        
    Returns:
        Decimal: Years of service
    """
    # Calculate days since hired
    days_employed = (datetime.utcnow() - hired_date).days
    
    # Convert to years (using 365.25 to account for leap years)
    years_employed = Decimal(str(days_employed)) / Decimal('365.25')
    
    return years_employed.quantize(Decimal('0.01'))

def calculate_leave_accrual(fte: Union[Decimal, float, str], service_years: Union[Decimal, float, str], 
                           leave_type: str, state: str = 'vic') -> Decimal:
    """
    Calculate leave accrual based on FTE, service years, and leave type.
    
    Args:
        fte: Full-time equivalent (0.0 to 1.0)
        service_years: Years of service
        leave_type: Type of leave ('annual_leave', 'sick_leave', 'personal_leave', 'bereavement_leave', 'long_service')
        state: State/territory for long service leave calculations
        
    Returns:
        Decimal: Hours of leave accrued per year
    """
    # Convert to Decimal for precision
    fte_dec = Decimal(str(fte))
    service_years_dec = Decimal(str(service_years))
    
    # Cap FTE at 1.0
    if fte_dec > Decimal('1.0'):
        fte_dec = Decimal('1.0')
    
    # Map standard leave types to accrual rates
    leave_map = {
        'annual_leave': 'holiday',
        'sick_leave': 'sick',
        'personal_leave': 'carers',
        'bereavement_leave': 'bereavement'
    }
    
    # Get leave type key
    leave_key = leave_map.get(leave_type, leave_type)
    
    # Calculate accrual for standard leave types
    if leave_key in LEAVE_ACCRUAL_RATES:
        accrual = LEAVE_ACCRUAL_RATES[leave_key] * fte_dec
        return accrual.quantize(Decimal('0.01'))
    
    # Calculate accrual for long service leave (only if eligible)
    if leave_type == 'long_service':
        # Check eligibility (typically 7-10 years depending on state)
        eligibility = {
            'vic': Decimal('7'),
            'act': Decimal('7'),
            'nsw': Decimal('10'),
            'qld': Decimal('10'),
            'sa': Decimal('10'),
            'wa': Decimal('10'),
            'tas': Decimal('10'),
            'nt': Decimal('10')
        }
        
        state_key = state.lower()
        eligible_years = eligibility.get(state_key, Decimal('7'))
        
        if service_years_dec >= eligible_years:
            accrual_rate = LONG_SERVICE_ACCRUAL_RATE.get(state_key, LONG_SERVICE_ACCRUAL_RATE['vic'])
            accrual = accrual_rate * fte_dec
            return accrual.quantize(Decimal('0.01'))
        else:
            return Decimal('0')
    
    # Default case
    return Decimal('0')

def get_user_leave_summary(user: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get a user's leave summary from their record.
    
    Args:
        user: User document from database
        
    Returns:
        Dict: Dictionary with leave balances and other details
    """
    # Get leave entitlements
    entitlements = user.get('leave_entitlements', {})
    
    # Standard leave types
    leave_types = ['holiday', 'sick', 'carers', 'bereavement']
    
    # Build summary
    summary = {}
    
    for leave_type in leave_types:
        accrued = Decimal(str(entitlements.get(f'{leave_type}_accrued', 0)))
        taken = Decimal(str(entitlements.get(f'{leave_type}_taken', 0)))
        balance = accrued - taken
        
        # Map internal leave type names to user-friendly names
        display_names = {
            'holiday': 'Annual Leave',
            'sick': 'Sick Leave',
            'carers': 'Personal/Carer\'s Leave',
            'bereavement': 'Bereavement Leave'
        }
        
        summary[leave_type] = {
            'name': display_names.get(leave_type, leave_type.title()),
            'accrued': float(accrued.quantize(Decimal('0.01'))),
            'taken': float(taken.quantize(Decimal('0.01'))),
            'balance': float(balance.quantize(Decimal('0.01')))
        }
    
    # Check for long service leave eligibility
    employment_details = user.get('employment_details', {})
    hired_date_raw = employment_details.get('hired_date')
    
    if hired_date_raw:
        # Handle various date formats
        hired_date = None
        if isinstance(hired_date_raw, datetime):
            hired_date = hired_date_raw
        elif isinstance(hired_date_raw, dict) and '$date' in hired_date_raw:
            # MongoDB date format
            date_str = hired_date_raw['$date']
            if isinstance(date_str, str):
                if date_str.endswith('Z'):
                    date_str = date_str[:-1]
                hired_date = datetime.fromisoformat(date_str)
            elif isinstance(date_str, (int, float)):
                hired_date = datetime.fromtimestamp(date_str / 1000.0)
        elif isinstance(hired_date_raw, str):
            try:
                hired_date = datetime.fromisoformat(hired_date_raw.rstrip('Z'))
            except ValueError:
                pass
        
        if hired_date:
            service_years = calculate_service_period(hired_date)
            
            # Determine long service leave eligibility (using VIC as default)
            eligible_years = Decimal('7')  # VIC standard
            if service_years >= eligible_years:
                # Add long service leave to summary
                summary['long_service'] = {
                    'name': 'Long Service Leave',
                    'accrued': float((service_years - eligible_years) * LONG_SERVICE_ACCRUAL_RATE['vic']),
                    'taken': float(Decimal(str(entitlements.get('long_service_taken', 0)))),
                    'balance': float((service_years - eligible_years) * LONG_SERVICE_ACCRUAL_RATE['vic'] - 
                                    Decimal(str(entitlements.get('long_service_taken', 0)))),
                    'eligible': True
                }
            else:
                # Add long service leave eligibility information
                summary['long_service'] = {
                    'name': 'Long Service Leave',
                    'accrued': 0,
                    'taken': 0,
                    'balance': 0,
                    'eligible': False,
                    'years_to_eligible': float((eligible_years - service_years).quantize(Decimal('0.01'))),
                    'eligible_date': (hired_date + timedelta(days=int(eligible_years * 365.25))).strftime('%Y-%m-%d')
                }
    
    return summary