"""
NSW-specific payroll configurations for 2024-25 financial year.
Must be used with main payroll_config.py.
"""
from decimal import Decimal

STATE_CONFIG = {
    'payroll_tax': {
        'threshold': Decimal('1200000'),
        'rate': Decimal('0.0475'),
        'grouping_rules': 'State-wide grouping applies',
        'monthly_return_required': True
    },
    'workers_comp': {
        'base_rate': Decimal('0.015'),  # Varies by industry
        'dust_diseases_levy': Decimal('0.003')  # NSW-specific
    },
    'long_service_leave': {
        'accrual_rate': Decimal('0.0133'),  # 1.33% per year
        'accrual_basis': 'ordinary_hours',
        'vesting_period': 5  # Years until portable
    },
    'other_levies': {
        'apprenticeship_levy': Decimal('0.012')  # NSW specific
    }
}
