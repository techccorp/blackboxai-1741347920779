"""
Static payroll configuration settings for Australian payroll systems.
Comprehensive coverage of employment taxation requirements for 2024-25 financial year.
Company-specific details are retrieved dynamically from MongoDB.
"""
from decimal import Decimal

# Default payment reference prefix
DEFAULT_PAYMENT_REFERENCE_PREFIX = "PAY"

# Superannuation configuration
SUPERANNUATION = {
    'rate': Decimal('0.115'),  # 11.5% for 2024-25
    'max_quarterly_base': Decimal('62270'),  # 2023-24 value, update when 2024-25 available
    'minimum_employee_earnings': Decimal('0')  # No minimum since July 2022
}

# Medicare components
MEDICARE = {
    'levy_rate': Decimal('0.02'),
    'low_income_thresholds': {
        'single': Decimal('24276'),      # 2023-24 values - update when available
        'family': Decimal('40939'),      # with 1 child
        'child_base': Decimal('3756')    # Additional per child
    },
    'surcharge': {
        'tiers': {
            'tier1': {'threshold': Decimal('93000'), 'rate': Decimal('0.01')},
            'tier2': {'threshold': Decimal('108000'), 'rate': Decimal('0.0125')},
            'tier3': {'threshold': Decimal('144000'), 'rate': Decimal('0.015')}
        },
        'family_threshold_multiplier': 2
    }
}

# Standard hours calculations (38hr week basis)
STANDARD_HOURS = {
    'weekly': Decimal('38'),
    'fortnightly': Decimal('76'),
    'monthly': Decimal('164.67'),  # 38 * 52 / 12
    'annual': Decimal('1976')       # 38 * 52
}

# Leave entitlements (annual full-time)
LEAVE_ENTITLEMENTS = {
    'annual_leave': {
        'hours': Decimal('152'),        # 4 weeks
        'accrual_type': 'continuous',
        'loading_rate': Decimal('0.175') # 17.5% loading (award-dependent)
    },
    'personal_carers_leave': {
        'hours': Decimal('76'),         # 10 days
        'accrual_type': 'continuous'
    },
    'compassionate_leave': {
        'hours': Decimal('15.2'),        # 2 days
        'accrual_type': 'per_instance'
    },
    'long_service_leave': {
        'accrual_rate': Decimal('0.013'),  # Varies by state - NSW example
        'accrual_type': 'annual'
    }
}

# Tax brackets (2024-25 Resident and Non-Resident)
TAX_BRACKETS = {
    'resident': [
        {'threshold': Decimal('0'),      'rate': Decimal('0'),   'base': Decimal('0')},
        {'threshold': Decimal('18201'),   'rate': Decimal('0.16'), 'base': Decimal('0')},
        {'threshold': Decimal('45001'),   'rate': Decimal('0.30'), 'base': Decimal('4288')},
        {'threshold': Decimal('135001'), 'rate': Decimal('0.37'), 'base': Decimal('31288')},
        {'threshold': Decimal('190001'), 'rate': Decimal('0.45'), 'base': Decimal('51413')}
    ],
    'non_resident': [
        {'threshold': Decimal('0'),      'rate': Decimal('0.325'), 'base': Decimal('0')},
        {'threshold': Decimal('140001'), 'rate': Decimal('0.37'),  'base': Decimal('45500')},
        {'threshold': Decimal('190001'), 'rate': Decimal('0.45'),  'base': Decimal('75100')}
    ]
}

# Study and Training Support Loans
STUDENT_LOANS = {
    'repayment_thresholds': {
        'hecs_help': Decimal('51550'),       # 2023-24 values
        'tsl': Decimal('51550'),
        'sfss': Decimal('65638')
    },
    'repayment_rates': [
        (Decimal('51550'),  Decimal('0.01')),
        (Decimal('59118'),  Decimal('0.02')),
        # ... full tier structure
        (Decimal('151201'), Decimal('0.10'))
    ]
}

# Tax Offsets
TAX_OFFSETS = {
    'LITO': {
        'max_offset': Decimal('700'),
        'min_threshold': Decimal('37500'),
        'withdrawal_rate': Decimal('0.05')
    },
    'SAPTO': {
        'single_threshold': Decimal('32279'),
        'family_threshold': Decimal('57966'),
        'shade_out_rate': Decimal('0.125')
    }
}

# Payroll Tax thresholds (NSW example - state-specific values would vary)
PAYROLL_TAX = {
    'nsw': {
        'threshold': Decimal('1200000'),
        'rate': Decimal('0.0475')
    }
}

# Other configuration
PERIOD_DIVISORS = {
    'weekly': Decimal('52'),
    'fortnightly': Decimal('26'),
    'monthly': Decimal('12')
}

# Workers Compensation (example NSW rates)
WORKERS_COMPENSATION = {
    'nsw_base_rate': Decimal('0.015')  # Varies by industry
}

# Reportable employer super contributions threshold
REPORTABLE_SUPER_THRESHOLD = Decimal('0')  # All contributions reportable

# Leave type mapping (MongoDB field names to standard names)
LEAVE_MAPPING = {
    'annual_leave_balance': 'annual_leave',
    'annual_leave_used': 'annual_leave_taken',
    'sick_leave_balance': 'sick_leave',
    'sick_leave_used': 'sick_leave_taken',
    'personal_leave_balance': 'personal_leave',
    'personal_leave_used': 'personal_leave_taken',
    'long_service_leave_balance': 'long_service_leave',
    'long_service_leave_used': 'long_service_leave_taken'
}
