# routes/auth/__init__.py
from flask import Blueprint

# Create auth blueprint that matches name from auth_routes.py
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Import routes
from . import routes

# Export the blueprint with the same name as the original
auth = auth_bp