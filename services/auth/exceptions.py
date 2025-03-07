class IDServiceError(Exception):
    """Base exception for ID service errors"""
    pass

class SequenceInitializationError(IDServiceError):
    """Raised when sequence initialization fails"""
    pass

class InvalidAreaCodeError(IDServiceError):
    """Raised when an invalid work area is provided"""
    pass
