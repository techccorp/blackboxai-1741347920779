# ------------------------------------------------------------
#                   config/payroll/__init__.py
# ------------------------------------------------------------
"""
Payroll Configuration Package
------------------------------
Provides unified access to national and state-specific payroll configurations.
Handles dynamic loading of state rules and validation of configuration integrity.

Usage:
    from config.payroll import get_national_config, get_state_config

    national_cfg = get_national_config()
    vic_config = get_state_config('vic')
"""

import importlib
from decimal import Decimal
from typing import Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

# National configuration (core payroll rules)
NATIONAL_CONFIG: Dict[str, Any] = None

# State configuration cache
STATE_CONFIG_CACHE: Dict[str, Dict[str, Any]] = {}

# Exception classes
class PayrollConfigError(Exception):
    """Base exception for configuration errors"""

class InvalidStateCodeError(PayrollConfigError):
    """Invalid state/territory code provided"""

class StateConfigLoadError(PayrollConfigError):
    """Error loading state configuration"""

def _load_national_config() -> Dict[str, Any]:
    """Load and validate the national payroll configuration"""
    try:
        from . import payroll_config
    except ImportError as e:
        logger.error("National payroll config missing: %s", e)
        raise PayrollConfigError("Missing national payroll configuration") from e

    required_keys = {
        'SUPERANNUATION',
        'TAX_BRACKETS',
        'MEDICARE',
        'LEAVE_ENTITLEMENTS'
    }

    config = {k: getattr(payroll_config, k) for k in dir(payroll_config) 
              if not k.startswith('_')}

    missing = required_keys - config.keys()
    if missing:
        logger.critical("Missing required national config keys: %s", missing)
        raise PayrollConfigError(f"Missing national config keys: {missing}")

    return config

def get_national_config() -> Dict[str, Any]:
    """Get validated national payroll configuration"""
    global NATIONAL_CONFIG
    if NATIONAL_CONFIG is None:
        NATIONAL_CONFIG = _load_national_config()
    return NATIONAL_CONFIG.copy()

def validate_state_code(state_code: str) -> None:
    """Validate state/territory code format"""
    valid_codes = {
        'nsw', 'vic', 'qld', 'wa', 
        'sa', 'tas', 'act', 'nt'
    }
    if state_code.lower() not in valid_codes:
        raise InvalidStateCodeError(f"Invalid state code: {state_code}")

def load_state_config(state_code: str) -> Dict[str, Any]:
    """Load and validate state-specific configuration"""
    state_code = state_code.lower()
    validate_state_code(state_code)

    if state_code in STATE_CONFIG_CACHE:
        return STATE_CONFIG_CACHE[state_code]

    try:
        module = importlib.import_module(
            f'.{state_code}Tax_config',
            package='config.payroll'
        )
        config = getattr(module, 'STATE_CONFIG')
    except (ImportError, AttributeError) as e:
        logger.error("State config load failed for %s: %s", state_code, e)
        raise StateConfigLoadError(
            f"Failed to load config for {state_code}"
        ) from e

    # Validate minimum required structure
    required_keys = {'payroll_tax', 'workers_comp'}
    missing = required_keys - config.keys()
    if missing:
        logger.error("State %s config missing keys: %s", state_code, missing)
        raise StateConfigLoadError(
            f"{state_code} config missing keys: {missing}"
        )

    # Cache and return
    STATE_CONFIG_CACHE[state_code] = config
    return config

def get_state_config(state_code: str) -> Dict[str, Any]:
    """Get validated state-specific configuration"""
    state_code = state_code.lower()
    if state_code in STATE_CONFIG_CACHE:
        return STATE_CONFIG_CACHE[state_code].copy()
    
    return load_state_config(state_code).copy()

def get_combined_config(state_code: str) -> Dict[str, Any]:
    """Get merged national + state configuration"""
    national = get_national_config()
    state = get_state_config(state_code)
    
    return {
        'national': national,
        'state': state,
        'composite': {
            # Example combined value
            'total_tax_rates': {
                'national': national['TAX_BRACKETS'],
                'state_payroll': state['payroll_tax']['rate']
            }
        }
    }

# Initialize national config on import
try:
    NATIONAL_CONFIG = _load_national_config()
except PayrollConfigError as e:
    logger.critical("Critical payroll configuration error: %s", e)
    raise

__all__ = [
    'get_national_config',
    'get_state_config',
    'get_combined_config',
    'PayrollConfigError',
    'InvalidStateCodeError',
    'StateConfigLoadError'
]
