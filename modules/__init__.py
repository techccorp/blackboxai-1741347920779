"""
Core modules package initialization.
"""
from .module_manager import module_manager, init_app, get_service, cleanup

__all__ = ['module_manager', 'init_app', 'get_service', 'cleanup']
