# ------------------------------------------------------------
# utils/validation_utils.py
# ------------------------------------------------------------
import re
import uuid
from datetime import datetime
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

def validate_request_data(required_fields):
    """
    Decorator to validate required fields in request data
    
    Usage:
    @validate_request_data(['payroll_id', 'password'])
    def login():
        # Your route logic here
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "message": "No data provided"
                    }), 400

                missing_fields = [
                    field for field in required_fields 
                    if not data.get(field)
                ]

                if missing_fields:
                    return jsonify({
                        "success": False,
                        "message": f"Missing required fields: {', '.join(missing_fields)}"
                    }), 400

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Request validation error: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "Invalid request data"
                }), 400

        return decorated_function
    return decorator

def validate_id_format(id_str, prefix):
    """
    Validate ID format (e.g., USR-XX123456, BUS-XXXXXXXX, etc.)
    """
    if not isinstance(id_str, str):
        return False
        
    patterns = {
        'USR': r'^USR-[A-Z]{2}[0-9]{6}$',
        'BUS': r'^BUS-[A-Z0-9]{8}$',
        'VEN': r'^VEN-[0-9]{4}-[0-9]{2}$',
        'WRK': r'^WRK-[A-Z0-9]{8}$',
        'CNY': r'^CNY-[0-9]{4}$',
        'WAI': r'^WAI-[0-9]{4}-[0-9]{4}$',
        'EMP': r'^EMP-[0-9]{4}-[0-9]{4}-[0-9]{6}$',
        'BOH': r'^BOH-[A-Z]{3}-[0-9]{3}$',
        'FOH': r'^FOH-[A-Z]{3}-[0-9]{3}$'
    }
    
    pattern = patterns.get(prefix)
    if not pattern:
        return False
        
    return bool(re.match(pattern, id_str))

def validate_payroll_id(payroll_id):
    """
    Validate the format of a payroll ID.
    
    Valid format: D{work_area_letter}-{6 digits}
    Example: DK-308020 (Kitchen), DB-631353 (Bar)
    
    Args:
        payroll_id: The payroll ID to validate
        
    Returns:
        bool: True if the payroll ID is valid, False otherwise
    """
    # Check if the payroll ID matches the pattern
    pattern = r'^D[KBROFPSGW]-\d{6}$'
    return bool(re.match(pattern, payroll_id))

def validate_uuid(uuid_str):
    """
    Validate UUID format
    """
    try:
        uuid.UUID(str(uuid_str))
        return True
    except (ValueError, AttributeError):
        return False

def validate_email(email):
    """
    Validate email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email)))

def validate_date_format(date_str):
    """
    Validate date format (YYYY-MM-DD)
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False

def validate_phone_number(phone):
    """
    Validate phone number format
    """
    # Remove any spaces, dashes, or parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', str(phone))
    # Check if it matches international format
    return bool(re.match(r'^\+?[0-9]{10,15}$', cleaned))

def validate_required_fields(data, required_fields):
    """
    Validate presence of required fields in data
    Returns (is_valid, missing_fields)
    """
    if not isinstance(data, dict):
        return False, ["Data must be a dictionary"]
        
    missing = [field for field in required_fields if not data.get(field)]
    return len(missing) == 0, missing

def validate_field_length(value, min_length=None, max_length=None):
    """
    Validate field length
    """
    if not value:
        return False
        
    length = len(str(value))
    
    if min_length and length < min_length:
        return False
    if max_length and length > max_length:
        return False
        
    return True

def validate_numeric_range(value, min_value=None, max_value=None):
    """
    Validate numeric value range
    """
    try:
        num = float(value)
        if min_value is not None and num < min_value:
            return False
        if max_value is not None and num > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False

def log_validation_error(context, error_message):
    """
    Log validation errors
    """
    logger.error(f"Validation Error - {context}: {error_message}")

def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal
    """
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename)

def validate_business_data(business_data):
    """
    Validate business data structure for business entities
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required = ['company_name', 'company_id', 'director_name', 'ACN']
    missing = [f for f in required if not business_data.get(f)]
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")
    
    # Company ID validation
    company_id = business_data.get('company_id', '')
    if company_id and not validate_id_format(company_id, 'CNY'):
        errors.append("Invalid company ID format (should be CNY-XXXX)")
    
    # Company name validation
    name = business_data.get('company_name', '')
    if not validate_field_length(name, min_length=2, max_length=100):
        errors.append("Company name must be between 2 and 100 characters")
    
    # Head office validation if provided
    head_office = business_data.get('head_office', {})
    if head_office:
        address_fields = ['address', 'suburb', 'state', 'post_code']
        missing_address = [f for f in address_fields if not head_office.get(f)]
        if missing_address:
            errors.append(f"Missing head office details: {', '.join(missing_address)}")
    
    return len(errors) == 0, errors

def validate_venue_data(venue_data):
    """
    Validate venue data structure
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required = ['venue_id', 'venue_name', 'company_id', 'address', 'suburb', 'state', 'post_code']
    missing = [f for f in required if not venue_data.get(f)]
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")
    
    # Venue ID validation
    venue_id = venue_data.get('venue_id', '')
    if venue_id and not validate_id_format(venue_id, 'VEN'):
        errors.append("Invalid venue ID format (should be VEN-XXXX-XX)")
    
    # Name validation
    name = venue_data.get('venue_name', '')
    if not validate_field_length(name, min_length=2, max_length=100):
        errors.append("Venue name must be between 2 and 100 characters")
    
    # Company ID validation
    company_id = venue_data.get('company_id', '')
    if company_id and not validate_id_format(company_id, 'CNY'):
        errors.append("Invalid company ID format (should be CNY-XXXX)")
    
    # Address validation
    address = venue_data.get('address', '')
    if not validate_field_length(address, min_length=5, max_length=200):
        errors.append("Address must be between 5 and 200 characters")
    
    # Contact validation (if provided)
    phone = venue_data.get('phone')
    if phone and not validate_phone_number(phone):
        errors.append("Invalid phone number format")
    
    # Email validation (if provided)
    email = venue_data.get('email')
    if email and not validate_email(email):
        errors.append("Invalid email format")
    
    return len(errors) == 0, errors

def validate_work_area_data(work_area_data):
    """
    Validate work area data structure
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required = ['work_area_name', 'work_area_id']
    missing = [f for f in required if not work_area_data.get(f)]
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")
    
    # Work area ID validation
    work_area_id = work_area_data.get('work_area_id', '')
    if work_area_id and not validate_id_format(work_area_id, 'WAI'):
        errors.append("Invalid work area ID format (should be WAI-XXXX-XXXX)")
    
    # Name validation
    name = work_area_data.get('work_area_name', '')
    if not validate_field_length(name, min_length=2, max_length=50):
        errors.append("Work area name must be between 2 and 50 characters")
    
    return len(errors) == 0, errors

def validate_user_data(user_data):
    """
    Validate user data structure
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required = ['linking_id', 'payroll_id', 'company_id', 'company_name', 
                'first_name', 'last_name', 'work_email', 'personal_contact']
    missing = [f for f in required if not user_data.get(f)]
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")
    
    # Linking ID validation
    linking_id = user_data.get('linking_id', '')
    if linking_id and not validate_id_format(linking_id, 'EMP'):
        errors.append("Invalid linking ID format (should be EMP-XXXX-XXXX-XXXXXX)")
    
    # Payroll ID validation
    payroll_id = user_data.get('payroll_id', '')
    if payroll_id and not validate_payroll_id(payroll_id):
        errors.append("Invalid payroll ID format (should be DX-XXXXXX)")
    
    # Email validation
    email = user_data.get('work_email', '')
    if email and not validate_email(email):
        errors.append("Invalid email format")
    
    # Phone validation
    phone = user_data.get('personal_contact', '')
    if phone and not validate_phone_number(phone):
        errors.append("Invalid phone number format")
    
    # Date of birth validation
    dob = user_data.get('date_of_birth')
    if dob:
        if isinstance(dob, dict) and '$date' in dob:
            # Handle MongoDB date format
            dob_str = dob['$date'][:10]  # Extract YYYY-MM-DD part
            if not validate_date_format(dob_str):
                errors.append("Invalid date of birth format")
        elif isinstance(dob, str):
            if not validate_date_format(dob):
                errors.append("Invalid date of birth format")
    
    return len(errors) == 0, errors