#-------------------------------------#
#        routes\auth\routes.py          #
#-------------------------------------#

import logging
from flask import request, jsonify, session, url_for, current_app
from werkzeug.exceptions import BadRequest, InternalServerError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from extensions import mongo
from utils.auth.auth_utils import validate_payroll_id, check_password
from . import auth_bp  # Import the blueprint from __init__.py

logger = logging.getLogger(__name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Handle user login with payroll_id and password. 
    Uses the 'business_users' collection, and checks 
    the hashed password in the password field.
    """
    try:
        data = request.get_json()
        payroll_id = data.get("payroll_id")
        password = data.get("password")

        # Basic checks
        if not (payroll_id and password):
            raise BadRequest("Missing required fields.")

        # Ensure format like 'D(K,R,O,F,P,S,G,W)-XXXXXX'
        if not validate_payroll_id(payroll_id):
            raise BadRequest("Invalid payroll ID format.")

        # Query the 'business_users' collection where payroll_id == payroll_id
        user = mongo.db.business_users.find_one({
            "payroll_id": payroll_id 
        })

        if not user:
            raise BadRequest("User  not found in business_users.")

        # Grab the hashed password from the password field
        hashed_pw = user["password"]  # Accessing the password directly

        # Compare the supplied plaintext password with the hashed password
        if not check_password(hashed_pw, password):
            raise BadRequest("Invalid password.")

        # If we reach here, login is successful
        session["user"] = payroll_id  # Store in session
        logger.info(f"User  {payroll_id} logged in successfully.")
        return jsonify({
            "success": True,
            "redirect_url": url_for("main_bp.home")
        }), 200

    except BadRequest as e:
        logger.error(f"Login error: {e.description}")
        return jsonify({"success": False, "error": e.description}), 400
    except Exception as e:
        logger.exception("An unexpected error occurred during login.")
        raise InternalServerError("An unexpected error occurred.")

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Log out the current user."""
    session.pop("user", None)
    return jsonify({"success": True}), 200

@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    """
    Handle Google login using an ID token.
    Validates the token and retrieves the user from the database.
    """
    try:
        token = request.json.get('id_token')
        client_id = current_app.config['GOOGLE_CLIENT_ID']
        
        # Validate Google token
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
        
        # Find user by work_email
        user = mongo.db.business_users.find_one({
            "work_email": id_info['email'],
            "auth_provider": {"$in": ["google", None]}
        })

        if not user:
            return jsonify({
                "success": False,
                "error": "No company account linked to this Google identity"
            }), 404

        # Update session with dual identifiers
        session["user"] = {
            "payroll_id": user["payroll_id"],
            "google_id": id_info["sub"],
            "auth_provider": "google"
        }
        
        return jsonify({"success": True, "redirect_url": url_for("main_bp.home")})
        
    except ValueError as e:
        return jsonify({"success": False, "error": "Invalid Google token"}), 401
    except Exception as e:
        logger.exception("An unexpected error occurred during Google login.")
        raise InternalServerError("An unexpected error occurred.")
