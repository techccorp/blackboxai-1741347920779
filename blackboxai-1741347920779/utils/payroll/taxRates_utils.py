"""
Utility functions for tax rate calculations and payroll processing.
"""
from decimal import Decimal
from typing import Dict, Union, Any
from datetime import datetime, date

# Tax rate brackets for 2024-25 (July 2024 - June 2025)
TAX_BRACKETS_2024_25 = [
    (0, 18200, 0, 0),                           # 0%
    (18201, 45000, 0.19, 0),                    # 19%
    (45001, 120000, 0.325, 5092),               # 32.5%
    (120001, 180000, 0.37, 29467),              # 37%
    (180001, float('inf'), 0.45, 51667)         # 45%
]

# Medicare levy rate
MEDICARE_LEVY_RATE = Decimal('0.02')  # 2%

# Medicare levy thresholds for 2024-25
MEDICARE_THRESHOLDS_2024_25 = {
    'individual': {
        'min': Decimal('24276'),  # No Medicare levy
        'max': Decimal('30399')   # Reduced Medicare levy up to this amount
    },
    'family': {
        'min': Decimal('40939'),  # Base threshold
        'max': Decimal('51166'),  # Upper threshold
        'per_child': Decimal('3760')  # Additional threshold per dependent child
    },
    'senior': {
        'min': Decimal('38271'),
        'max': Decimal('47847')
    }
}

# Low Income Tax Offset (LITO) for 2024-25
LITO_2024_25 = {
    'max_offset': Decimal('700'),
    'base_threshold': Decimal('37500'),
    'taper_rate_1': Decimal('0.05'),   # 5% reduction for income between $37,500 and $45,000
    'threshold_2': Decimal('45000'),
    'taper_rate_2': Decimal('0.015')   # 1.5% reduction for income between $45,000 and $66,667
}

# Super guarantee rate (as of 2024)
SUPER_RATE = Decimal('0.11')  # 11%

# Standard full-time hours per week
STANDARD_WEEKLY_HOURS = Decimal('38')


def get_current_financial_year() -> str:
    """
    Get the current financial year in YYYY-YY format.
    
    In Australia, financial year runs from July 1 to June 30.
    
    Returns:
        str: Current financial year (e.g., "2024-25")
    """
    today = date.today()
    if today.month >= 7:  # July to December
        return f"{today.year}-{str(today.year + 1)[-2:]}"
    else:  # January to June
        return f"{today.year - 1}-{str(today.year)[-2:]}"


def get_tax_brackets(financial_year: str = None) -> list:
    """
    Get tax brackets for the specified financial year.
    
    Args:
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        list: List of tax brackets
    """
    # Default to current financial year
    if financial_year is None:
        financial_year = get_current_financial_year()
    
    # Select tax brackets based on financial year
    if financial_year == "2024-25":
        return TAX_BRACKETS_2024_25
    # Future financial years can be added here
    # elif financial_year == "2025-26":
    #     return TAX_BRACKETS_2025_26
    
    # Default to latest known brackets
    return TAX_BRACKETS_2024_25


def get_medicare_thresholds(financial_year: str = None) -> Dict:
    """
    Get Medicare levy thresholds for the specified financial year.
    
    Args:
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        Dict: Medicare levy thresholds
    """
    # Default to current financial year
    if financial_year is None:
        financial_year = get_current_financial_year()
    
    # Select thresholds based on financial year
    if financial_year == "2024-25":
        return MEDICARE_THRESHOLDS_2024_25
    # Future financial years can be added here
    # elif financial_year == "2025-26":
    #     return MEDICARE_THRESHOLDS_2025_26
    
    # Default to latest known thresholds
    return MEDICARE_THRESHOLDS_2024_25


def get_lito_params(financial_year: str = None) -> Dict:
    """
    Get Low Income Tax Offset parameters for the specified financial year.
    
    Args:
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        Dict: LITO parameters
    """
    # Default to current financial year
    if financial_year is None:
        financial_year = get_current_financial_year()
    
    # Select parameters based on financial year
    if financial_year == "2024-25":
        return LITO_2024_25
    # Future financial years can be added here
    # elif financial_year == "2025-26":
    #     return LITO_2025_26
    
    # Default to latest known parameters
    return LITO_2024_25


def calculate_hourly_rate(annual_salary: Union[Decimal, float, str], hours_per_week: Union[Decimal, float, int, None] = None) -> Decimal:
    """
    Calculate hourly rate from annual salary.
    
    Args:
        annual_salary: Annual salary amount
        hours_per_week: Weekly hours (default: 38)
        
    Returns:
        Decimal: Hourly rate
    """
    # Convert to Decimal for precision
    annual = Decimal(str(annual_salary))
    
    # Default to standard full-time hours if not specified
    hours = Decimal(str(hours_per_week)) if hours_per_week is not None else STANDARD_WEEKLY_HOURS
    
    # Calculate hourly rate (annual / (52 weeks * hours per week))
    hourly_rate = annual / (Decimal('52') * hours)
    
    return hourly_rate.quantize(Decimal('0.01'))


def calculate_annual_salary(hourly_rate: Union[Decimal, float, str], hours_per_week: Union[Decimal, float, int, None] = None) -> Decimal:
    """
    Calculate annual salary from hourly rate.
    
    Args:
        hourly_rate: Hourly pay rate
        hours_per_week: Weekly hours (default: 38)
        
    Returns:
        Decimal: Annual salary
    """
    # Convert to Decimal for precision
    hourly = Decimal(str(hourly_rate))
    
    # Default to standard full-time hours if not specified
    hours = Decimal(str(hours_per_week)) if hours_per_week is not None else STANDARD_WEEKLY_HOURS
    
    # Calculate annual salary (hourly * hours per week * 52 weeks)
    annual_salary = hourly * hours * Decimal('52')
    
    return annual_salary.quantize(Decimal('0.01'))


def calculate_superannuation(gross_pay: Union[Decimal, float, str]) -> Decimal:
    """
    Calculate superannuation amount based on gross pay.
    
    Args:
        gross_pay: Gross pay amount
        
    Returns:
        Decimal: Superannuation amount
    """
    # Convert to Decimal for precision
    gross = Decimal(str(gross_pay))
    
    # Calculate super (using SUPER_RATE constant)
    super_amount = gross * SUPER_RATE
    
    return super_amount.quantize(Decimal('0.01'))


def calculate_lito(annual_salary: Union[Decimal, float, str], financial_year: str = None) -> Decimal:
    """
    Calculate Low Income Tax Offset (LITO).
    
    Args:
        annual_salary: Annual salary amount
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        Decimal: LITO amount
    """
    # Convert to Decimal for precision
    annual = Decimal(str(annual_salary))
    
    # Get LITO parameters
    lito_params = get_lito_params(financial_year)
    
    # Calculate LITO based on income
    if annual <= lito_params['base_threshold']:
        # Full offset
        return lito_params['max_offset']
    elif annual <= lito_params['threshold_2']:
        # First taper rate applies
        reduction = (annual - lito_params['base_threshold']) * lito_params['taper_rate_1']
        return max(Decimal('0'), lito_params['max_offset'] - reduction)
    else:
        # Second taper rate applies
        reduction_1 = (lito_params['threshold_2'] - lito_params['base_threshold']) * lito_params['taper_rate_1']
        reduction_2 = (annual - lito_params['threshold_2']) * lito_params['taper_rate_2']
        return max(Decimal('0'), lito_params['max_offset'] - reduction_1 - reduction_2)


def calculate_medicare_levy(annual_salary: Union[Decimal, float, str], 
                          family_status: str = 'individual', 
                          num_dependents: int = 0,
                          senior: bool = False,
                          financial_year: str = None) -> Decimal:
    """
    Calculate Medicare Levy based on income and family status.
    
    Args:
        annual_salary: Annual salary amount
        family_status: 'individual' or 'family'
        num_dependents: Number of dependent children (for family threshold)
        senior: Whether the taxpayer is a senior
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        Decimal: Medicare Levy amount
    """
    # Convert to Decimal for precision
    annual = Decimal(str(annual_salary))
    
    # Get Medicare thresholds
    thresholds = get_medicare_thresholds(financial_year)
    
    # Determine applicable threshold
    if senior:
        min_threshold = thresholds['senior']['min']
        max_threshold = thresholds['senior']['max']
    elif family_status == 'family':
        # Family threshold increases with each dependent child
        min_threshold = thresholds['family']['min'] + (thresholds['family']['per_child'] * Decimal(str(num_dependents)))
        max_threshold = thresholds['family']['max'] + (thresholds['family']['per_child'] * Decimal(str(num_dependents)))
    else:
        min_threshold = thresholds['individual']['min']
        max_threshold = thresholds['individual']['max']
    
    # Calculate Medicare Levy
    if annual <= min_threshold:
        # No Medicare Levy
        return Decimal('0')
    elif annual <= max_threshold:
        # Reduced Medicare Levy
        # Formula: 10% of (income - min_threshold)
        return (annual - min_threshold) * Decimal('0.10')
    else:
        # Full Medicare Levy (2%)
        return annual * MEDICARE_LEVY_RATE


def calculate_annual_tax(annual_salary: Union[Decimal, float, str], financial_year: str = None) -> Decimal:
    """
    Calculate annual tax based on Australian tax brackets.
    
    Args:
        annual_salary: Annual salary amount
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        Decimal: Annual tax amount
    """
    # Convert to Decimal for precision
    annual = Decimal(str(annual_salary))
    
    # Get tax brackets for the relevant financial year
    tax_brackets = get_tax_brackets(financial_year)
    
    # Find applicable tax bracket
    for min_income, max_income, rate, base_tax in tax_brackets:
        if annual >= min_income and annual <= max_income:
            # Calculate tax using the formula: base_tax + (income - min_income) * rate
            tax = Decimal(str(base_tax)) + (annual - Decimal(str(min_income))) * Decimal(str(rate))
            
            # Apply Low Income Tax Offset (LITO)
            lito = calculate_lito(annual, financial_year)
            tax = max(Decimal('0'), tax - lito)
            
            return tax.quantize(Decimal('0.01'))
    
    # Default case (should not reach here with infinity in brackets)
    return Decimal('0')


def calculate_period_amounts(annual_salary: Union[Decimal, float, str], 
                           pay_frequency: str = 'fortnightly', 
                           include_medicare: bool = True,
                           family_status: str = 'individual',
                           num_dependents: int = 0,
                           senior: bool = False,
                           financial_year: str = None) -> Dict[str, Decimal]:
    """
    Calculate payment amounts for different periods based on annual salary.
    
    Args:
        annual_salary: Annual salary amount
        pay_frequency: Pay frequency ('weekly', 'fortnightly', 'monthly')
        include_medicare: Whether to include Medicare levy in tax calculation
        family_status: 'individual' or 'family' for Medicare levy
        num_dependents: Number of dependent children for Medicare levy
        senior: Whether the taxpayer is a senior
        financial_year: Financial year in YYYY-YY format (default: current)
        
    Returns:
        Dict: Dictionary of payment amounts for the period
    """
    # Convert to Decimal for precision
    annual = Decimal(str(annual_salary))
    
    # Define period divisors
    divisors = {
        'weekly': Decimal('52'),
        'fortnightly': Decimal('26'),
        'monthly': Decimal('12')
    }
    
    # Get divisor for frequency
    divisor = divisors.get(pay_frequency.lower(), Decimal('26'))  # Default to fortnightly
    
    # Calculate gross for period
    gross = annual / divisor
    
    # Calculate annual tax
    annual_tax = calculate_annual_tax(annual, financial_year)
    
    # Calculate Medicare levy if included
    medicare_levy = Decimal('0')
    if include_medicare:
        medicare_levy = calculate_medicare_levy(
            annual, 
            family_status, 
            num_dependents, 
            senior, 
            financial_year
        )
    
    # Calculate total tax (income tax + Medicare levy)
    total_tax = annual_tax + medicare_levy
    
    # Calculate tax for period
    tax = total_tax / divisor
    
    # Calculate net for period
    net = gross - tax
    
    # Calculate super for period
    super_amount = gross * SUPER_RATE
    
    # Calculate hourly rate based on standard hours per period
    hours_per_period = {
        'weekly': Decimal('38'),          # 38 hours per week
        'fortnightly': Decimal('76'),     # 76 hours per fortnight
        'monthly': Decimal('165.33')      # Average hours per month
    }
    
    hours = hours_per_period.get(pay_frequency.lower(), Decimal('76'))
    hourly_rate = annual / (divisors.get(pay_frequency.lower(), Decimal('26')) * hours_per_period.get(pay_frequency.lower(), Decimal('76'))) * hours
    
    return {
        'gross': gross.quantize(Decimal('0.01')),
        'tax': tax.quantize(Decimal('0.01')),
        'medicare': (medicare_levy / divisor).quantize(Decimal('0.01')),
        'net': net.quantize(Decimal('0.01')),
        'super': super_amount.quantize(Decimal('0.01')),
        'hourly_rate': (annual / (divisors['weekly'] * Decimal('38'))).quantize(Decimal('0.01')),
        'hours': hours
    }


def get_user_ytd_amounts(user: Dict[str, Any]) -> Dict[str, Decimal]:
    """
    Get year-to-date amounts from user record.
    
    Args:
        user: User document from database
        
    Returns:
        Dict: Dictionary of YTD amounts
    """
    # Get accrued employment data
    accrued = user.get('accrued_employment', {})
    
    # Get salary YTD
    salary_ytd = Decimal(str(accrued.get('salary_ytd', 0)))
    
    # Get tax withheld YTD
    tax_ytd = Decimal(str(accrued.get('tax_withheld_ytd', accrued.get('tax_withheld', 0))))
    
    # Get Medicare levy YTD
    medicare_ytd = Decimal(str(accrued.get('medicare_ytd', 0)))
    
    # Get super YTD if available, otherwise calculate based on salary
    super_ytd = Decimal(str(accrued.get('super_ytd', 0)))
    if super_ytd == 0:
        super_ytd = salary_ytd * SUPER_RATE
    
    return {
        'earnings': salary_ytd.quantize(Decimal('0.01')),
        'tax': tax_ytd.quantize(Decimal('0.01')),
        'medicare': medicare_ytd.quantize(Decimal('0.01')),
        'super': super_ytd.quantize(Decimal('0.01'))
    }