# ------------------------------------------------------------
#                     config/__init__.py
# ------------------------------------------------------------
from .base_config import AppConfig as Config, get_config
from .redis_config import RedisConfig, RedisConfigError
from .payroll import (
    PayrollConfigError,
    InvalidStateCodeError,
    StateConfigLoadError,
    get_national_config,
    get_state_config,
    get_combined_config
)

__all__ = [
    # Core configuration
    'Config',
    'get_config',
    
    # Redis configuration
    'RedisConfig',
    'RedisConfigError',
    
    # Payroll configuration
    'PayrollConfigError',
    'InvalidStateCodeError',
    'StateConfigLoadError',
    'get_national_config',
    'get_state_config',
    'get_combined_config'
]

# Add version information
__version__ = '2.3.0'
__config_version__ = '2024.2'
