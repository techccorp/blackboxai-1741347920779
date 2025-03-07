# ------------------------------------------------------------
# routes/__init__.py
# ------------------------------------------------------------
from flask import Flask
import logging
from typing import List, Tuple
from werkzeug.routing import Rule

# Import all route blueprints
try:
    from .auth_routes import auth  # Original import
except ImportError:
    from .auth import auth_bp as auth  # Fallback to new structure

from .allergen_routes import allergens
# from .home_routes import home  # Module not found - removed
from .business.businessAPI_routes import business_api
from .business.routes import business
from .error_routes import error_routes
from .finance_routes import finance
from .common_routes import common
from .google_routes import google_api
from .employment_routes import employment
from .product_routes import products
from .recipeSearch_routes import recipe_search
from .googleTasks_routes import google_tasks
from .notes_routes import notes
from .resource_routes import resource
from .businessUsers_routes import business_users

logger = logging.getLogger(__name__)

def init_routes(app: Flask) -> None:
    """
    Initialize all application routes.
    
    Args:
        app: Flask application instance
    
    Raises:
        RuntimeError: If route initialization fails
    """
    try:
        logger.info("Initializing application routes...")
        
        # Core routes
        app.register_blueprint(auth_bp)  # Updated to use auth_bp instead of auth
        app.register_blueprint(common)
        app.register_blueprint(error_routes)
        # app.register_blueprint(home)  # Module not found - removed
        
        # Business functionality routes
        app.register_blueprint(business)
        app.register_blueprint(business_api)
        app.register_blueprint(finance)
        app.register_blueprint(employment)
        app.register_blueprint(business_users)
        
        # Product and recipe routes
        app.register_blueprint(products)
        app.register_blueprint(recipe_search)
        app.register_blueprint(allergens)
        
        # Google API integration routes
        app.register_blueprint(google_api)
        app.register_blueprint(google_tasks)
        
        # Additional functionality routes
        app.register_blueprint(notes)
        app.register_blueprint(resource)
        
        # Log registered routes in debug mode
        if app.debug:
            log_registered_routes(app)
            
        logger.info("Route initialization completed successfully")
        
    except Exception as e:
        logger.critical(f"Failed to initialize routes: {str(e)}")
        raise RuntimeError(f"Route initialization failed: {str(e)}")

def get_registered_routes(app: Flask) -> List[Tuple[str, str, set]]:
    """
    Get all registered routes in the application.
    
    Args:
        app: Flask application instance
        
    Returns:
        List of tuples containing (endpoint, route_path, methods)
    """
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append((
            rule.endpoint,
            rule.rule,
            rule.methods - {'HEAD', 'OPTIONS'}  # Exclude default HTTP methods
        ))
    return sorted(routes, key=lambda x: x[1])  # Sort by route path

def log_registered_routes(app: Flask) -> None:
    """
    Log all registered routes for debugging purposes.
    
    Args:
        app: Flask application instance
    """
    logger.debug("Registered routes:")
    for endpoint, rule, methods in get_registered_routes(app):
        logger.debug(f"{endpoint}: {rule} [{', '.join(methods)}]")

# Export initialization function
__all__ = ['init_routes', 'get_registered_routes']