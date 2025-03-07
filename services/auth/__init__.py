# services/auth/__init__.py
"""
Authentication Services Module

Provides ID generation and validation services with production-grade error handling.
Includes:
- IDService: Main service class for generating and validating various identifiers
- Custom exceptions for error handling (IDServiceError, IDGenerationError, etc)
"""

from .exceptions import (
    IDServiceError,
    SequenceInitializationError,
    InvalidAreaCodeError
)
from .id_service import (
    IDService,
    IDGenerationError,
    InvalidIDError
)

__all__ = [
    'IDService',
    'IDServiceError',
    'SequenceInitializationError',
    'InvalidAreaCodeError',
    'IDGenerationError',
    'InvalidIDError'
]
