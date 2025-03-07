from flask import Blueprint, request, jsonify, session, current_app
from functools import wraps
from utils import (
    add_venue_to_business,
    add_work_area_to_venue,
    validate_business_structure,
    get_business_hierarchy,
    lookup_venue,
    lookup_work_area
)
from config import Config
from models import get_db
import logging
from datetime import datetime

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize blueprint
business_api = Blueprint('business_api', __name__, url_prefix='/api/business')

def login_required(f):
    """Decorator to ensure the user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@business_api.route('/venue/update', methods=['POST'])
@login_required
def update_venue():
    """Create or update a venue"""
    try:
        db = get_db()
        data = request.json
        venue_id = data.get('venueId')

        if not venue_id:
            # Create new venue
            id_service = current_app.config['ID_SERVICE']
            venue_id = id_service.generate_venue_id()

            venue_data = {
                'venue_id': venue_id,
                'name': data.get('name'),
                'address': data.get('address'),
                'contact': data.get('contact'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            result = add_venue_to_business(
                db,
                session.get('business_setup_id'),
                venue_data
            )

            if not result:
                raise Exception('Failed to create venue')

            return jsonify(venue_data), 201

        else:
            # Update existing venue
            result = db.businesses.update_one(
                {'venues.venue_id': venue_id},
                {'$set': {
                    'venues.$.name': data.get('name'),
                    'venues.$.address': data.get('address'),
                    'venues.$.contact': data.get('contact'),
                    'venues.$.updated_at': datetime.utcnow()
                }}
            )

            if result.modified_count == 0:
                raise Exception('Venue not found or no changes made')

            return jsonify({
                'venue_id': venue_id,
                **data
            }), 200

    except Exception as e:
        logger.error(f'Error updating venue: {str(e)}')
        return jsonify({'error': str(e)}), 500

@business_api.route('/workarea/create', methods=['POST'])
@login_required
def create_work_area():
    """Create a new work area"""
    try:
        db = get_db()
        data = request.json

        id_service = current_app.config['ID_SERVICE']
        work_area_id = id_service.generate_work_area_id()

        work_area_data = {
            'work_area_id': work_area_id,
            'name': data.get('name'),
            'venue_id': data.get('venue_id'),
            'description': data.get('description', ''),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = add_work_area_to_venue(
            db,
            session.get('business_setup_id'),
            data.get('venue_id'),
            work_area_data
        )

        if not result:
            raise Exception('Failed to create work area')

        return jsonify(work_area_data), 201

    except Exception as e:
        logger.error(f'Error creating work area: {str(e)}')
        return jsonify({'error': str(e)}), 500

@business_api.route('/complete-setup', methods=['POST'])
@login_required
def complete_setup():
    """Complete the business setup process"""
    try:
        db = get_db()
        business_id = session.get('business_setup_id')

        # Validate business structure
        is_valid, issues = validate_business_structure(db, business_id)
        if not is_valid:
            return jsonify({
                'error': 'Invalid business structure',
                'issues': issues
            }), 400

        # Update business status to active
        result = db.businesses.update_one(
            {'business_id': business_id},
            {'$set': {
                'status': 'active',
                'completed_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )

        if result.modified_count == 0:
            raise Exception('Business not found or no changes made')

        # Clear setup session data
        session.pop('business_setup_id', None)

        return jsonify({'status': 'success', 'message': 'Business setup completed successfully'}), 200

    except Exception as e:
        logger.error(f'Error completing business setup: {str(e)}')
        return jsonify({'error': str(e)}), 500

@business_api.route('/venues/<venue_id>', methods=['GET'])
@login_required
def get_venue(venue_id):
    """Retrieve details of a venue"""
    try:
        db = get_db()
        venue_data = lookup_venue(db, venue_id)
        if venue_data:
            return jsonify(venue_data), 200
        return jsonify({'error': 'Venue not found'}), 404
    except Exception as e:
        logger.error(f'Error retrieving venue: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@business_api.route('/work-areas/<work_area_id>', methods=['GET'])
@login_required
def get_work_area(work_area_id):
    """Retrieve details of a work area"""
    try:
        db = get_db()
        work_area_data = lookup_work_area(db, work_area_id)
        if work_area_data:
            return jsonify(work_area_data), 200
        return jsonify({'error': 'Work area not found'}), 404
    except Exception as e:
        logger.error(f'Error retrieving work area: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@business_api.route('/hierarchy/<business_id>', methods=['GET'])
@login_required
def get_hierarchy(business_id):
    """Retrieve the full hierarchy of a business"""
    try:
        db = get_db()
        hierarchy = get_business_hierarchy(db, business_id)
        if hierarchy:
            return jsonify(hierarchy), 200
        return jsonify({'error': 'Business not found'}), 404
    except Exception as e:
        logger.error(f'Error retrieving hierarchy: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
