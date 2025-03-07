#!/usr/bin/env python3
"""
routes/onboarding_routes.py
---------------------------
This module defines the onboarding blueprint to handle the web-based company onboarding
process. It serves the onboarding UI and exposes an API endpoint (/api/onboard) that
validates incoming data, generates IDs, processes venues and head office details, and
inserts the final document into the MongoDB "business_entities" collection.
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

logger = logging.getLogger(__name__)

# Define the blueprint with URL prefix /onboarding.
onboarding_bp = Blueprint(
    'onboarding',
    __name__,
    template_folder='onboarding',  # expects templates/onboarding/comapny.html
    static_folder='js/onbarding',   # expects static/js/onbarding/company.js
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
    # (Optional) Implement ACN checksum validation if needed.
    return True

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

def generate_simplified_id(prefix, unique_id=None):
    """
    Generate a simplified unique ID using a prefix.
    Uses the first 4 digits of a UUID's integer representation.
    """
    base_id = str(uuid.uuid4().int)[:4]
    if unique_id:
        return f"{prefix}-{unique_id}-{base_id}"
    return f"{prefix}-{base_id}"

def ensure_complete_company_data(company):
    """
    Ensure that the company document includes all required keys.
    If a key is missing, a default value is provided.
    """
    defaults = {
        "company_id": "",
        "company_name": "",
        "director_name": "",
        "ACN": "",
        "admin_user_id": "",
        "head_office": {},
        "venues": []
    }
    for key, default in defaults.items():
        company.setdefault(key, default)
    
    for venue in company.get("venues", []):
        venue_defaults = {
            "venue_id": "",
            "venue_name": "",
            "venue_manager_id": "",
            "venue_manager_name": "",
            "workareas": []
        }
        for key, default in venue_defaults.items():
            venue.setdefault(key, default)
    return company

def generate_work_area_id(company_number, venue_suffix, wa_start, work_area_index):
    """
    Generate a work_area_id in the format:
        WAI-<company_number>-<venue_suffix><sequential two-digit number>
    """
    sequence_num = wa_start + work_area_index
    return f"WAI-{company_number}-{venue_suffix}{str(sequence_num).zfill(2)}"

def process_single_venue(venue_data, company_number, default_company_name):
    """
    Process a single venue entry.
    - Defaults the venue name to the company name if not provided.
    - Generates a random two-digit suffix for the venue_id.
    - Generates a unique venue_manager_id.
    - Processes work areas and generates work_area_ids.
    """
    venue = {}
    # Use provided venue name or default to the company name.
    venue_name = venue_data.get("name", "").strip() or default_company_name
    random_suffix = str(uuid.uuid4().int)[:2]
    venue['venue_id'] = f"VEN-{company_number}-{random_suffix}"
    venue['venue_name'] = venue_name
    venue['venue_manager_name'] = venue_data.get("manager", "").strip()
    venue['venue_manager_id'] = f"EMP-{company_number}-{str(uuid.uuid4().int)[:4]}"
    
    # Process work areas.
    work_areas = venue_data.get("work_areas", [])
    wa_start = random.randint(10, 99)
    workareas = []
    for i, wa_name in enumerate(work_areas):
        wa_id = generate_work_area_id(company_number, random_suffix, wa_start, i)
        workareas.append({
            "work_area_id": wa_id,
            "work_area_name": wa_name.strip()
        })
    venue['workareas'] = workareas
    return venue

def process_multi_venue(venue_data, company_number, venue_suffix):
    """
    Process a venue entry for multi venue or multi outlet companies.
    - Uses the provided venue_suffix to generate the venue_id.
    - Generates a unique venue_manager_id.
    - Processes work areas and generates work_area_ids.
    """
    venue = {}
    venue['venue_id'] = f"VEN-{company_number}-{venue_suffix}"
    venue['venue_name'] = venue_data.get("name", "").strip()
    venue['venue_manager_name'] = venue_data.get("manager", "").strip()
    venue['venue_manager_id'] = f"EMP-{company_number}-{str(uuid.uuid4().int)[:4]}"
    
    work_areas = venue_data.get("work_areas", [])
    wa_start = random.randint(10, 99)
    workareas = []
    for i, wa_name in enumerate(work_areas):
        wa_id = generate_work_area_id(company_number, venue_suffix, wa_start, i)
        workareas.append({
            "work_area_id": wa_id,
            "work_area_name": wa_name.strip()
        })
    venue['workareas'] = workareas
    return venue

def save_company_document(db, company):
    """
    Insert the final company document into the collection defined in configuration.
    The collection name is retrieved from the app config (defaulting to "business_entities").
    """
    try:
        collection_name = current_app.config.get("COLLECTION_BUSINESSES", "business_entities")
        result = db[collection_name].insert_one(company)
        return result.inserted_id
    except Exception as e:
        logger.exception("Failed to insert company document into MongoDB")
        raise e

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@onboarding_bp.route('/', methods=['GET'])
def onboarding_ui():
    """
    Serve the onboarding user interface.
    The UI HTML is expected to be at templates/onboarding/comapny.html.
    """
    return render_template('comapny.html')

@onboarding_bp.route('/api/onboard', methods=['POST'])
def handle_onboarding():
    """
    Handle the onboarding form submission.
    Validates incoming data, generates IDs, processes head office and venue details,
    and inserts the final company document into MongoDB.
    """
    try:
        data = request.get_json()
        logger.info("Received onboarding data: %s", data)
        
        # Validate required fields.
        required_fields = [
            'company_name', 'director_name', 'acn', 'admin_user_name',
            'head_office', 'venues', 'company_type'
        ]
        if not all(field in data for field in required_fields):
            logger.error("Missing required fields in the onboarding data")
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate ACN.
        if not validate_acn(data['acn']):
            logger.error("Invalid ACN provided: %s", data['acn'])
            return jsonify({'error': 'Invalid ACN'}), 400

        # Validate head office phone.
        head_office = data['head_office']
        if not validate_aus_phone_number(head_office.get('phone', '')):
            logger.error("Invalid head office phone number: %s", head_office.get('phone', ''))
            return jsonify({'error': 'Invalid head office phone number'}), 400

        # Generate company and admin user IDs.
        company_id = generate_simplified_id("CNY")
        try:
            company_number = company_id.split("-")[1]
        except IndexError:
            company_number = "0000"
        admin_user_id = f"CNY-{company_number}-{str(uuid.uuid4().int)[:4]}"

        # Build company document.
        company = OrderedDict()
        company['company_id'] = company_id
        company['company_name'] = data['company_name'].strip()
        company['director_name'] = data['director_name'].strip()
        company['ACN'] = data['acn'].strip()
        company['admin_user_id'] = admin_user_id

        # Process head office details.
        company['head_office'] = {
            "address": head_office.get("address", "").strip(),
            "suburb": head_office.get("suburb", "").strip(),
            "state": head_office.get("state", "").strip(),
            "post_code": head_office.get("post_code", "").strip(),
            "contact": {
                "phone": head_office.get("phone", "").strip(),
                "email": head_office.get("email", "").strip()
            }
        }

        # Process venues.
        venues = []
        company_type = str(data.get("company_type", "1")).strip()  # "1": Single, "2": Multi Venue, "3": Multi Outlet
        received_venues = data.get("venues", [])
        if company_type == "1":
            # For a single venue, use the first entry.
            if not received_venues:
                logger.error("No venue data provided for single venue type.")
                return jsonify({'error': 'No venue data provided'}), 400
            venue = process_single_venue(received_venues[0], company_number, company['company_name'])
            venues.append(venue)
        elif company_type in ["2", "3"]:
            # For multi venue/outlet, assign sequential venue suffixes.
            start_suffix = random.randint(10, 99)
            for i, venue_data in enumerate(received_venues):
                venue_suffix = str(start_suffix + i).zfill(2)
                venue = process_multi_venue(venue_data, company_number, venue_suffix)
                venues.append(venue)
        else:
            logger.error("Invalid company type: %s", company_type)
            return jsonify({'error': 'Invalid company type'}), 400

        company['venues'] = venues

        # Ensure complete company data.
        company = ensure_complete_company_data(company)

        # Insert the document into MongoDB.
        # Retrieve the database from the global MongoDB client.
        db = current_app.config['MONGO_CLIENT'][current_app.config.get('MONGO_DBNAME')]
        inserted_id = save_company_document(db, company)
        logger.info("Company document inserted with id: %s", inserted_id)

        return jsonify({
            'message': 'Company onboarded successfully',
            'inserted_id': str(inserted_id)
        }), 200

    except Exception as e:
        logger.exception("Error processing onboarding data")
        return jsonify({'error': str(e)}), 500
