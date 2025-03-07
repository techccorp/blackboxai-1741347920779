"""
Victoria-specific payroll configurations for 2024-25 financial year.
Must be used with main payroll_config.py.
"""
from decimal import Decimal

STATE_CONFIG = {
    'payroll_tax': {
        'threshold': Decimal('700000'),
        'rate': Decimal('0.0485'),
        'regional_concession': Decimal('0.01'),  # Regional employer discount
        'grouping_rules': 'Economic entity grouping'
    },
    'workers_comp': {
        'base_rate': Decimal('0.016'),  # Average rate
        'mental_health_levy': Decimal('0.005')  # Vic-specific
    },
    'long_service_leave': {
        'accrual_rate': Decimal('0.0127'),  # 1.27% per year
        'accrual_basis': 'ordinary_earnings',
        'vesting_period': 7  # Years until portable
    },
    'other_levies': {
        'metropolitan_levy': Decimal('0.0005')  # Melbourne CBD employers
    }
}
