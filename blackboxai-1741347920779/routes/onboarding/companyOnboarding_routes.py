#!/usr/bin/env python3
"""
routes/onboarding/companyOnboarding_routes.py
---------------------------
This module defines the onboarding blueprint to handle the web-based company onboarding
process. It serves the onboarding UI and exposes an API endpoint (/api/onboard) that
validates incoming data, generates IDs, processes venues and head office details, and
creates documents in the respective MongoDB collections.
"""

import os
import re
import uuid
import random
import json
import logging
from datetime import datetime
from collections import OrderedDict

from flask import Blueprint, request, jsonify, render_template, current_app
from services.auth.id_service import IDService
from utils.business_utils import (
    create_business, 
    add_venue_to_business, 
    add_work_area_to_venue,
    assign_user_to_business,
    assign_user_to_work_area
)

logger = logging.getLogger(__name__)

# Define the blueprint with URL prefix /onboarding.
onboarding_bp = Blueprint(
    'onboarding',
    __name__,
    template_folder='onboarding',  # expects templates/onboarding/company_onboarding.html
    static_folder='js/onboarding',  # expects static/js/onboarding/company.js
    url_prefix='/onboarding'
)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def validate_acn(acn):
    """
    Validate the Australian Company Number (ACN).
    A valid ACN should contain exactly 9 digits (ignoring spaces and punctuation).
    """
    acn_digits = ''.join(filter(str.isdigit, acn))
    if len(acn_digits) != 9:
        return False
    
    # Apply ACN checksum validation
    weights = [8, 7, 6, 5, 4, 3, 2, 1]
    digits = [int(digit) for digit in acn_digits[:-1]]
    weighted_sum = sum(w * d for w, d in zip(weights, digits))
    remainder = weighted_sum % 10
    check_digit = 10 - remainder if remainder else 0
    
    return check_digit == int(acn_digits[-1])

def validate_aus_phone_number(phone):
    """
    Validate an Australian phone number.
    Accepts numbers starting with '+61' or '0'.
    For numbers with '+61', expects 9 digits after the country code.
    For numbers starting with '0', expects 10 digits in total.
    """
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("+61"):
        return len(phone) == 12 and phone[1:].isdigit()
    elif phone.startswith("0"):
        return len(phone) == 10 and phone.isdigit()
    return False

def validate_email(email):
    """
    Basic email validation
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def ensure_complete_company_data(company_data):
    """
    Prepare complete company data for further processing
    """
    head_office = company_data.get('head_office', {})
    
    business_data = {
        'company_name': company_data.get('company_name', '').strip(),
        'venue_type': company_data.get('venue_type', 'hospitality'),
        'head_office': {
            'address': head_office.get('address', '').strip(),
            'suburb': head_office.get('suburb', '').strip(),
            'state': head_office.get('state', '').strip(),
            'post_code': head_office.get('post_code', '').strip(),
            'contact': {
                'phone': head_office.get('phone', '').strip(),
                'email': head_office.get('email', '').strip()
            }
        }
    }
    
    return business_data

def process_venues_and_work_areas(db, company_id, venues_data, id_service):
    """
    Process venues and their work areas, creating appropriate records
    
    Args:
        db: MongoDB database connection
        company_id: Company ID string
        venues_data: List of venue data from the request
        id_service: Instance of IDService for ID generation
        
    Returns:
        List of venue IDs created
    """
    venue_ids = []
    
    for venue_data in venues_data:
        # Prepare venue data for insertion
        venue_info = {
            'venue_name': venue_data.get('name', '').strip(),
            'address': venue_data.get('address', '').strip(),
            'suburb': venue_data.get('suburb', '').strip(),
            'state': venue_data.get('state', '').strip(),
            'post_code': venue_data.get('postcode', '').strip(),
            'phone': venue_data.get('phone', '').strip(),
            'email': venue_data.get('email', '').strip()
        }
        
        # Add venue to business
        venue_doc = add_venue_to_business(db, company_id, venue_info)
        if not venue_doc:
            logger.error(f"Failed to add venue {venue_info['venue_name']} to company {company_id}")
            continue
            
        venue_id = venue_doc['venue_id']
        venue_ids.append(venue_id)
        
        # Process venue manager if provided
        if venue_data.get('manager'):
            manager_id = venue_data.get('venue_manager_id') or id_service.generate_linking_id(company_id, venue_id)
            venue_manager_role = {
                'role_id': 'FOH-EXE-306',  # Venue Manager role ID
                'role_name': 'Venue Manager',
                'payroll_id': id_service.generate_payroll_id('venue'),
            }
            
            # Assign manager to business
            assign_user_to_business(db, company_id, manager_id, 'manager')
            
            # Add work area for 'venue' if not already included
            venue_work_area = {
                'work_area_name': 'Venue',
                'description': 'Main venue management area'
            }
            venue_work_area_doc = add_work_area_to_venue(db, company_id, venue_id, venue_work_area)
            
            if venue_work_area_doc:
                # Assign manager to the venue work area
                assign_user_to_work_area(
                    db, 
                    company_id, 
                    venue_id, 
                    venue_work_area_doc['work_area_id'], 
                    manager_id, 
                    venue_manager_role
                )
        
        # Process work areas
        work_areas = venue_data.get('work_areas', [])
        for work_area_data in work_areas:
            # Skip 'venue' work area if already created for manager
            if work_area_data.get('work_area_name', '').lower() == 'venue' and venue_work_area_doc:
                continue
                
            work_area_info = {
                'work_area_name': work_area_data.get('work_area_name', ''),
                'description': work_area_data.get('description', f"Work area for {work_area_data.get('work_area_name', '')}")
            }
            
            work_area_doc = add_work_area_to_venue(db, company_id, venue_id, work_area_info)
            if not work_area_doc:
                logger.error(f"Failed to add work area {work_area_info['work_area_name']} to venue {venue_id}")
        
    return venue_ids

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@onboarding_bp.route('/', methods=['GET'])
def onboarding_ui():
    """
    Serve the onboarding user interface.
    """
    return render_template('company_onboarding.html')

@onboarding_bp.route('/api/onboard', methods=['POST'])
def handle_onboarding():
    """
    Handle the onboarding form submission.
    Validates incoming data, generates IDs, processes head office and venue details,
    and creates documents in the respective MongoDB collections.
    """
    try:
        # Get database connection from app config
        db = current_app.config['MONGO_CLIENT'][current_app.config.get('MONGO_DBNAME', 'dashboard_db')]
        
        # Initialize ID service
        id_service = IDService(db)
        
        # Parse and validate request data
        data = request.get_json()
        logger.info("Received onboarding data: %s", data)
        
        # Validate required fields
        required_fields = ['company_name', 'Director_name', 'ACN', 'admin_user_name', 'head_office', 'venues']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate ACN
        if not validate_acn(data['ACN']):
            logger.error(f"Invalid ACN provided: {data['ACN']}")
            return jsonify({'error': 'Invalid ACN format'}), 400
        
        # Validate head office phone and email
        head_office = data.get('head_office', {})
        if not validate_aus_phone_number(head_office.get('contact', {}).get('phone', '')):
            logger.error(f"Invalid head office phone number")
            return jsonify({'error': 'Invalid head office phone number'}), 400
            
        if not validate_email(head_office.get('contact', {}).get('email', '')):
            logger.error(f"Invalid head office email")
            return jsonify({'error': 'Invalid head office email'}), 400
        
        # Create admin user ID if not provided
        admin_user_id = data.get('admin_user_id', '')
        if not admin_user_id:
            # Generate a new company ID
            company_id = id_service.generate_company_id()
            admin_user_id = f"{company_id}-{str(uuid.uuid4().hex[:4])}"
        
        # Create business document
        business_data = ensure_complete_company_data(data)
        company_doc = create_business(db, admin_user_id, business_data)
        
        if not company_doc:
            logger.error("Failed to create company document")
            return jsonify({'error': 'Failed to create company document'}), 500
        
        company_id = company_doc['company_id']
        
        # Process venues and work areas
        venue_ids = process_venues_and_work_areas(db, company_id, data.get('venues', []), id_service)
        
        if not venue_ids:
            logger.error("No venues were successfully created")
            return jsonify({'error': 'No venues were successfully created'}), 500
        
        # Return success response with created company ID
        return jsonify({
            'message': 'Company onboarded successfully',
            'company_id': company_id,
            'venues_created': len(venue_ids)
        }), 200
        
    except Exception as e:
        logger.exception("Error processing onboarding data")
        return jsonify({'error': str(e)}), 500