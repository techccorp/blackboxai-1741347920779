"""
Queensland-specific payroll configurations for 2024-25 financial year.
Must be used with main payroll_config.py.
"""
from decimal import Decimal

STATE_CONFIG = {
    'payroll_tax': {
        'threshold': Decimal('1300000'),
        'rate': Decimal('0.0475'),
        'deduction_entitlement': Decimal('92000'),  # QLD specific
        'grouping_rules': 'Single entity basis'
    },
    'workers_comp': {
        'base_rate': Decimal('0.014'),
        'coal_levy': Decimal('0.020')  # Mining industry surcharge
    },
    'long_service_leave': {
        'accrual_rate': Decimal('0.0166'),  # 1.66% per year
        'portable_schemes': ['construction', 'cleaning']
    },
    'other_levies': {
        'mental_health_levy': Decimal('0.0025')  # QLD specific
    }
}
